#!/usr/bin/env -S python3 -B

# NOTE: If you are using an alpine docker image
# such as pyaction-lite, the -S option above won't
# work. The above line works fine on other linux distributions
# such as debian, etc, so the above line will work fine
# if you use pyaction:4.0.0 or higher as your base docker image.

import sys
import os
import json
import argparse
from string import Template
from dataclasses import dataclass
from localization_differ import Settings, LocalizationDiffer
import uuid

if __name__ == "__main__" :
    # Rename these variables to something meaningful
    # input1 = sys.argv[1]
    # input2 = sys.argv[2]

    # FIXME
    os.popen("git config --global --add safe.directory /github/workspace").read()

    print("args:", sys.argv)
    # parser.add_argument("-b", "--branch", default="main", help="Branch to operate on")
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-d", "--base_dir", default="assets/base/assets/localization", help="Directory containing localization files")
    parser.add_argument("-f", "--base_file", default="en.json", help="Native translation file")
    parser.add_argument("-b", "--branch", default="loc_wf", help="Branch to operate on")
    parser.add_argument("-c", "--commit", default="afea18f6f1cda5c8db8e31dfec8edf7e04624f90", help="Old commit to check against. Defaults to last")
    parser.add_argument("-m", "--maintainers", default="localization_maintainers.json", help="Path fo maintainers JSON")
    parser.add_argument("-t", "--template", default=".github/scripts/template.yml", help="Path to YAML markdown template")
    parser.add_argument("-s", "--disable_mentions", default="false", help="Disable mention links")
    parser.add_argument("-p", "--js_patch", default="false", help="Show git diff as json template (for larger repos)")
    parser.add_argument("-u", "--use_comments", default="false", help="Show templates as comments")
    # parser.add_argument("-", "--", default="", help="")

    args = parser.parse_args()
    settings = Settings(**args.__dict__)

    # with open(settings.maintainers, encoding="utf-8") as f:
    #     data =  json.load(f)
    #     print('maintainers', data)
    # with open(settings.base_dir + "/" + settings.base_file, encoding="utf-8") as f:
    #     data =  json.load(f)
    #     print('basefile', data)

    # EN_PATH = Path(settings.base_dir) / settings.base_file
    # EN_PATH_F = str(EN_PATH).replace('\\', '/')
    settings.branch = settings.branch.split('/')[-1]  # clean up ref
    if settings.commit is None:
        if os.name == 'nt':
            settings.commit = "HEAD^^"
        else:
            settings.commit = "HEAD^"
    settings.disable_mentions = settings.disable_mentions.lower() == 'true'
    settings.js_patch = settings.js_patch.lower() == 'true'
    settings.use_comments = settings.use_comments.lower() == 'true'

    
    # if "GITHUB_WORKSPACE" in os.environ :
    #     ws_dir = os.environ.get("GITHUB_WORKSPACE", "/github/workspace")
    #     print("base_ls", os.listdir(settings.base_dir))
    #     print("ws_dir_ls", os.listdir(ws_dir))
    #     settings.base_dir = os.path.join(ws_dir, settings.base_dir)
    #     settings.maintainers = os.path.join(ws_dir, settings.maintainers)
    #     settings.template = os.path.join(ws_dir, settings.template)

    print(settings)

    processor = LocalizationDiffer(settings)
    processor.initialize()
    issue_body, issue_title, comments = processor.process()

    # This is how you produce workflow outputs.
    # Make sure corresponds to output variable names in action.yml
    # if "GITHUB_OUTPUT" in os.environ :
    #     with open(os.environ["GITHUB_OUTPUT"], "a", encoding='utf-8') as f :
    #         print("{0}={1}".format("issue-title", "issue_title"), file=f)
    #         print("{0}={1}".format("issue-body", issue_body), file=f)
    def write_output(name, value, is_json=False):
        delimiter = uuid.uuid4().hex  # a unique delimiter
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding='utf-8') as f:
            f.write(f"{name}<<{delimiter}\n")
            f.write(f"{is_json and json.dumps(value, ensure_ascii=False) or value}\n")
            f.write(f"{delimiter}\n")

    write_output("issue-title", issue_title)
    write_output("issue-body", issue_body)
    write_output("comments", comments, True)
