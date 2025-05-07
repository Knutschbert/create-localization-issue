from string import Template
import yaml
from dataclasses import dataclass
from pprint import pprint
import os
import json
from pathlib import Path
from typing import Dict
import sys
import glob
from collections import defaultdict
import pycountry
import argparse
import subprocess
import tempfile
from pprint import pprint

@dataclass
class LocalizationTemplates:
    main: Template
    change_added: Template
    change_removed: Template
    change_renamed: Template
    change_modified: Template
    missing_warning: Template
    issue_body: Template
    localization_body: Template

@dataclass
class Settings:
    base_dir: str
    base_file: str
    branch: str
    commit: str
    maintainers: str
    template: str
    disable_mentions: bool
    js_patch: bool
    use_comments: bool

class LocalizationDiffer:

    def __init__(self, settings: Settings):
        self.initialized = False
        self.settings = settings
        self.base_file_path = Path(settings.base_dir) / settings.base_file
        self.base_file_path_fwd = str(self.base_file_path).replace('\\', '/')
        self.comments_dict = {}
        self.comments = []
        self.tmpl = {}
        self.prev_en = {}
        self.current_en = {}
        self.comparison = {}
        self.changes = [[] for i in range(4)]
        self.language_map = {}  # type: Dict[str, Language]
        self.loc_files = []
        print('base path', self.base_file_path_fwd)
        pprint(self.settings)
    
    def initialize(self) -> bool:
        if not self.base_file_path.exists():
            print(f"{self.settings.base_file} not found in working tree.")
            return
        
        try:
            self.prev_en = self.load_previous_en_json()
        except Exception as e:
            print(f"Failed to load previous {self.settings.base_file}: {e}")
            return
        
        for loc_file in glob.glob(self.settings.base_dir+"/*.json"):
            if loc_file.endswith(os.path.basename(self.base_file_path)):
                continue
            self.loc_files.append(loc_file)
            base_name = os.path.basename(loc_file)
            lang = base_name.split('.')[0].upper().split('_')[0]
            language, _ = self.get_language_or_country(lang)
            self.language_map[base_name] = language
        # self.loc_files = [x for x in glob.glob(self.settings.base_dir+"/*.json") if not x.endswith(os.path.basename(self.base_file_path))]
        
        self.tmpl = self.load_templates()
        self.current_en = self.load_json(self.base_file_path)
        self.lang_images = self.load_json("/scripts/language_images.json")
        self.comparison = self.compare_dicts(self.prev_en, self.current_en)
        self.format_changes_str()

        if not self:
            print(f"No changes in {self.settings.base_file} content.")
            return
        
        self.initialized = True
    
    def process(self) -> bool:
        # build list of maintainers
        maintainers = {}
        if Path(self.settings.maintainers).exists():
            maintainers = self.load_json(self.settings.maintainers)

        maintainers_md = defaultdict(list)
        for filename, users in maintainers.items():
            for user in users:
                if self.settings.disable_mentions:
                    user = user[1:]
                flag_link, country_info = self.get_language_flag_from_filename(filename, True)
                maintainers_md[user].append(f'<a href="#user-content-{filename}">{flag_link}</a>')
                # maintainers_md[user].append(f'[{filename}](#user-content-{filename})')

        # build json templates and missing list for each language
        language_details = []
        json_templates = self.format_lang_changes_str()    
        
        for key, (template_str, missing) in json_templates.items():
            base_name = os.path.basename(key)
            flag_url, country_info = self.get_language_flag_from_filename(base_name)

            if self.settings.js_patch:
                template_str = self.git_diff_against_head(".", key, template_str)

            warnings = []
            if len(missing):
                warnings.append("### Warnings")
                for key2 in missing:
                    warnings.append(self.tmpl.missing_warning.safe_substitute(**{"key": key2}))

            language_template = self.tmpl.localization_body.safe_substitute(**{
                "base_dir": self.settings.base_dir,
                "country_name": country_info and country_info.name or "",
                "loc_file": base_name,
                "flag_url": flag_url and flag_url or "",
                "branch": self.settings.branch,
                "json_template": template_str,
                "warnings": "\n\n".join(warnings)
            })
            language_details.append(language_template)

            # self.comments.append(json.dumps(language_template, ensure_ascii=False))
            if self.settings.use_comments:
                self.comments.append(language_template)
                self.comments_dict[key] = language_template
                print('adding comment')
        
        for k, v in self.comments_dict.items():
            file_name = f'comments/{key}.md'
            with open(file_name) as file:
                print('Saved', file_name)
                file.write(v)
        # build main issue body    
        git_rev_head = os.popen("git rev-parse HEAD").read()

        issue_title = "🔤 Localization update needed"

        language_details_str = ""
        if not self.settings.use_comments:
            language_details_str = "\n".join(language for language in language_details)
            print('adding details')
        
        issue_body = self.tmpl.issue_body.safe_substitute(**{
            "url_base_locfile": f"[{self.settings.base_file}](../blob/{self.settings.branch}/{self.base_file_path_fwd})",
            "branch": self.settings.branch,
            "url_start_commit": self.settings.commit,
            "url_end_commit": git_rev_head,
            "changes_renamed": "\n".join(change for change in self.changes[0]),
            "changes_added": "\n".join(change for change in self.changes[1]),
            "changes_changed": "\n".join(change for change in self.changes[2]),
            "changes_removed": "\n".join(change for change in self.changes[3]),
            "user_mentions": "\n".join([f' - {k}: {", ".join(v)}' for k, v in maintainers_md.items()]),
            "language_details": language_details_str
        })

        return issue_body, issue_title, self.comments
    
    def git_diff_against_head(self, repo_path: str, file_path: str, edited_content: str):
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmp_file:
            tmp_file.write(edited_content)
            tmp_file_path = tmp_file.name

        try:
            result = subprocess.run(
                ["git", "-C", repo_path, "diff", 
                 "--unified=1", 
                 "--patch", 
                 "--no-index", 
                 "--", file_path, 
                 tmp_file_path],
                capture_output=True,
                text=True
            )
            return result.stdout
        finally:
            os.remove(tmp_file_path)
        
    def get_language_or_country(self, lang: str) -> str:
        # Try to get the language by alpha2/3 first
        language = None
        country = None
        countries = None
        try:
            if len(lang) in (2, 3):
                language = pycountry.languages.get(**{f'alpha_{len(lang)}': lang})
        except Exception as ex:
            print(f'Exception {ex}')

        # Try to get alpha3 from country name ad query as lang
        if language is None:
            if len(lang) in (2, 3):
                country = pycountry.countries.get(**{f'alpha_{len(lang)}': lang})
            if country is not None:
                language = pycountry.languages.get(alpha_3=country.alpha_3)
        else:
            print(f'normal {language.name}')

        return language, country
    
    def get_language_flag_from_filename(self, filename: str, small=False):
        # split locales like en_us
        flag_url = None
        # lang = filename.split('.')[0].upper().split('_')[0]
        # language, _ = self.get_language_or_country(lang)
        language = self.language_map.get(os.path.basename(filename), None)
        if language is not None:
            if language.name in self.lang_images:
                size_attr = small and f'height="20"' or ''
                # flag_url = f"https://raw.githubusercontent.com/exyte/FlagAndCountryCode/refs/heads/main/Sources/FlagAndCountryCode/Resources/CountryFlags.xcassets/{country_code}.imageset/{country_code}.png"
                flag_url = f'<img {size_attr} alt="{language.name}" src="https://upload.wikimedia.org/wikipedia/commons/thumb/{self.lang_images[language.name]}" style="border-radius: 50%">'
            else:
                size_attr = small and f'height="20' or 'width="50"'
                flag_url = f'<img {size_attr} alt="{language.name}" src="https://unpkg.com/language-icons/icons/{language.alpha_2}.svg" style="border-radius: 50%">'
        return flag_url, language

    def get_commit_url(self, SHA: str):
        return f"[{SHA[:6]}](../commit/{SHA.replace('^','')})"

    def load_templates(self):
        # Load string templates from YAML file
        tmpl = None
        with open(self.settings.template, encoding='utf-8') as file:
            try:
                templates = yaml.safe_load(file)
                wrapped_templates = {key: Template(value) for key, value in templates.items()}
                tmpl = LocalizationTemplates(**wrapped_templates)
            except yaml.YAMLError as exc:
                print('YAML Error:', exc)
        return tmpl
    
    def load_json(self, path):
        # load generic json file
        with open(path, encoding="utf-8") as f:
            return json.load(f)
        
    def load_previous_en_json(self):
        prev_content = os.popen(f"git show {self.settings.commit}:{self.base_file_path_fwd}").read()
        return json.loads(prev_content)
    
    def compare_dicts(self, old: Dict[str,str], new: Dict[str,str]):
        old_s = set(old)
        new_s = set(new)
        added = new_s - old_s
        removed = old_s - new_s
        changed = {k for k in new_s & old_s if new[k] != old[k]}

        # find renamed entries
        renamed = []
        unmatched_added = set(added)
        unmatched_removed = set(removed)

        for old_key in removed:
            old_val = old[old_key]
            for new_key in added:
                if new_key in unmatched_added and old_val == new[new_key]:
                    renamed.append((old_key, new_key))
                    unmatched_removed.discard(old_key)
                    unmatched_added.discard(new_key)
                    break

        return unmatched_added, unmatched_removed, changed, renamed

    def format_changes_str(self):
        # Format changes to main file
        added, removed, changed, renamed = self.comparison

        change_handlers = [
            (renamed, self.tmpl.change_renamed, lambda k, v: {"key": k, "value": v}),
            (added, self.tmpl.change_added, lambda k: {"key": k, "value": self.current_en[k]}),
            (changed, self.tmpl.change_added, lambda k: {"key": k, "value_old": self.prev_en[k], "value_new": self.current_en[k]}),
            (removed, self.tmpl.change_removed, lambda k: {"key": k}),
        ]

        for idx, (items, template, fn) in enumerate(change_handlers):
            for item in items:
                if isinstance(item, tuple):
                    self.changes[idx].append(template.safe_substitute(**fn(*item)))
                else:
                    self.changes[idx].append(template.safe_substitute(**fn(item)))

    def format_lang_changes_str(self):
        # Create language-specific json template
        templates = {}
        added_en, removed_en, changed_en, renamed_en = self.comparison
        for file_name in self.loc_files:
            if file_name.endswith(self.settings.base_file):
                continue

            js_data = self.load_json(file_name)
            added, removed, _, renamed = self.compare_dicts(js_data, self.current_en)
            
            # use new json structure and populate with localized values. Also rename keys
            template = {k: js_data.get(k, self.current_en[k]) for k,v in self.current_en.items()}
            for name_old, name_new in renamed_en:
                if name_old in js_data:
                    template[name_new] = js_data[name_old]

            # Add comments to template
            template_str = json.dumps(template, indent=2, ensure_ascii=False)
            for add in added & added_en:  # new
                template_str = template_str.replace(f'  "{add}":', f'//  "{add}":')
            for add in added - added_en:  # missing
                template_str = template_str.replace(f'  "{add}":', f'//⚠️  "{add}":')
            for (old_ren, new_ren) in renamed_en:
                if new_ren not in added:
                    template_str = template_str.replace(f'  "{new_ren}":',
                                                        f'// renamed "{old_ren}" to "{new_ren}"\n  "{new_ren}"')
            
            templates[file_name] = (template_str, added - added_en)
        return templates
    
def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-d", "--base_dir", default="assets/base/assets/localization", help="Directory containing localization files")
    parser.add_argument("-f", "--base_file", default="en.json", help="Native translation file")
    # parser.add_argument("-b", "--branch", default="main", help="Branch to operate on")
    parser.add_argument("-b", "--branch", default="loc_wf", help="Branch to operate on")
    parser.add_argument("-c", "--commit", default="afea18f6f1cda5c8db8e31dfec8edf7e04624f90", help="Old commit to check against. Defaults to last")
    parser.add_argument("-m", "--maintainers", default="localization_maintainers.json", help="Path fo maintainers JSON")
    parser.add_argument("-t", "--template", default=".github/scripts/template.yml", help="Path to YAML markdown template")
    parser.add_argument("-s", "--disable_mentions", default=False, help="Disable mention links")
    parser.add_argument("-p", "--js_patch", default=False, help="Show git diff as json template (for larger repos)")
    # parser.add_argument("-", "--", default="", help="")

    args = parser.parse_args()
    settings = Settings(**args.__dict__)
    pprint(settings)

    # EN_PATH = Path(settings.base_dir) / settings.base_file
    # EN_PATH_F = str(EN_PATH).replace('\\', '/')
    settings.branch = settings.branch.split('/')[-1]  # clean up ref
    if settings.commit is None:
        if os.name == 'nt':
            settings.commit = "HEAD^^"
        else:
            settings.commit = "HEAD^"
            
    processor = LocalizationDiffer(settings)
    processor.initialize()
    issue_body, issue_title = processor.process()
    with open('out.md', 'w', encoding='utf-8') as file:
        file.write(issue_body)
        file.close()
    print(issue_title)
    # print(issue_body)
    

if __name__ == "__main__":
    main()