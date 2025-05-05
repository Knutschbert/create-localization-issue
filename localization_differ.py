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

class LocalizationDiffer:

    def __init__(self, settings: Settings):
        self.initialized = False
        self.settings = settings
        self.base_file_path = Path(settings.base_dir) / settings.base_file
        self.base_file_path_fwd = str(self.base_file_path).replace('\\', '/')
        self.tmpl = {}
        self.prev_en = {}
        self.current_en = {}
        self.comparison = {}
        self.changes = []
        print('base path', self.base_file_path_fwd)
    
    def initialize(self) -> bool:
        if not self.base_file_path.exists():
            print(f"{self.settings.base_file} not found in working tree.")
            return
        
        try:
            self.prev_en = self.load_previous_en_json()
        except Exception as e:
            print(f"Failed to load previous {self.settings.base_file}: {e}")
            return
        
        self.tmpl = self.load_templates()
        self.current_en = self.load_json(self.base_file_path)
        self.comparison = self.compare_dicts_new(self.prev_en, self.current_en)
        self.changes = self.format_changes_str()

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
                maintainers_md[user].append(f'[{filename}](#{filename})')

        # build json templates and missing list for each language
        language_details = []
        json_templates = self.format_lang_changes_str()    
        
        for key, (template_str, missing) in json_templates.items():
            flag_url, country_info = self.get_language_flag_from_filename(key)

            warnings = []
            if len(missing):
                warnings.append("### Warnings")
                for key2 in missing:
                    warnings.append(self.tmpl.missing_warning.safe_substitute(**{"key": key2}))

            language_details.append(self.tmpl.localization_body.safe_substitute(**{
                "country_name": country_info.name,
                "loc_file": key,
                "flag_url": flag_url,
                "branch": self.settings.branch,
                "json_template": template_str,
                "warnings": "\n\n".join(warnings)
            }))
        
        # build main issue body    
        git_rev_head = os.popen("git rev-parse HEAD").read()

        issue_title = "🔤 Localization update needed"
        
        issue_body = self.tmpl.issue_body.safe_substitute(**{
            "url_base_locfile": f"[{self.settings.base_file}](../blob/{self.settings.branch}/{self.base_file_path_fwd})",
            "branch": self.settings.branch,
            "url_start_commit": self.get_commit_url(self.settings.commit),
            "url_end_commit": self.get_commit_url(git_rev_head),
            "change_summary": "\n".join(change for change in self.changes),
            "user_mentions": "\n".join([f' - {k}: {", ".join(v)}' for k, v in maintainers_md.items()]),
            "language_details": "\n".join(language for language in language_details)
        })

        return issue_body, issue_title

    def get_language_flag_from_filename(self, filename: str):
        # tries to parse country code from language file name
        language_code = filename.split('.')[0].upper().split('_')[0]
        country_code = language_code
        country_info = pycountry.languages.get(alpha_2=language_code)
        if country_info is not None:
            country_code = country_info.alpha_2
            country = pycountry.countries.search_fuzzy(country_info.alpha_3)
            if country is not None:
                country_code = country[0].alpha_2
        flag_url = f"https://raw.githubusercontent.com/exyte/FlagAndCountryCode/refs/heads/main/Sources/FlagAndCountryCode/Resources/CountryFlags.xcassets/{country_code}.imageset/{country_code}.png"
        return flag_url, country_info

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
    
    def compare_dicts_new(self, old: Dict[str,str], new: Dict[str,str]):
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
        changes = []
        added, removed, changed, renamed = self.comparison

        change_handlers = [
            (renamed, self.tmpl.change_renamed, lambda k, v: {"key": k, "value": v}),
            (added, self.tmpl.change_added, lambda k: {"key": k, "value": self.current_en[k]}),
            (changed, self.tmpl.change_added, lambda k: {"key": k, "value_old": self.prev_en[k], "value_new": self.current_en[k]}),
            (removed, self.tmpl.change_removed, lambda k: {"key": k}),
        ]

        for items, template, fn in change_handlers:
            for item in items:
                if isinstance(item, tuple):
                    changes.append(template.safe_substitute(**fn(*item)))
                else:
                    changes.append(template.safe_substitute(**fn(item)))
        return changes

    def format_lang_changes_str(self):
        # Create language-specific json template
        templates = {}
        added_en, removed_en, changed_en, renamed_en = self.comparison
        for file_name in glob.glob(self.settings.base_dir+"/*.json"):
            if file_name.endswith(self.settings.base_file):
                continue

            js_data = self.load_json(file_name)
            added, removed, _, renamed = self.compare_dicts_new(js_data, self.current_en)
            
            # use new json structure and populate with localized values. Also rename keys
            template = {k: js_data.get(k, self.current_en[k]) for k,v in self.current_en.items()}
            for name_old, name_new in renamed_en:
                if name_old in js_data:
                    template[name_new] = js_data[name_old]

            # Add comments to template
            template_str = json.dumps(template, indent=4, ensure_ascii=False)
            for add in added & added_en:  # new
                template_str = template_str.replace(f'  "{add}":', f'//  "{add}":')
            for add in added - added_en:  # missing
                template_str = template_str.replace(f'  "{add}":', f'//⚠️  "{add}":')
            for (old_ren, new_ren) in renamed_en:
                if new_ren not in added:
                    template_str = template_str.replace(f'  "{new_ren}":',
                                                        f'// renamed "{old_ren}" to "{new_ren}"\n  "{new_ren}"')
            
            templates[os.path.basename(file_name)] = (template_str, added - added_en)
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