# create-localization-issue
A Github Action to generate Issues when base localization file is updated.
Generated Issues feature translator @ mentions as well as JSON templates which translators can directly use.

This action assumes that localization files are simple JSON files with a dictionary containing key-value pairs.

Example localization directory: [Link](https://github.com/Mythical-Github/ue4ss_installer_gui/tree/dev/assets/base/assets/localization)

<details>
<summary><b>Example en.json localization file</b></summary>

```json
{
  "add_directory_to_scan_for_games_button_text": "Add directory to scan for games",
  "add_game_by_game_directory": "Add game by game directory",
  "cleaning_up_temp_files_step_text": "Cleaning up temp files",
  "close_button_text": "Close",
  "discord_button_text": "Discord"
}
```
</details>


## Setup
This workflow will run the python script and create a new issue/comments.

Create a file containing github user tags of translators (default: `localization_maintainers.json`):
```json
{
    "de.json": ["@knutschbert"],
    "ua.json": ["@knutschbert"]
}
```
---
<details>
<summary><b>Example workflow</b></summary>


```yaml
name: (EZ) Create Localization Help Issue

on:
  workflow_dispatch:
    inputs:
      commit:
        description: 'Commit to compare to (last by default)'
        type: string
        default: 'afea18f6f1cda5c8db8e31dfec8edf7e04624f90'
        required: true
      template:
        description: 'Custom YAML template for Markdown (if needed)'
        type: string
        default: '/scripts/template.yml'
        required: true
      disable-mentions:
        description: 'Print mentions as string'
        type: choice
        options: [ 'True', 'False' ]
        default: 'False'
        required: true
      js-patch:
        description: 'Show JSON templates as diff'
        required: true
        type: choice
        options: [ 'True', 'False' ]
        default: 'False'
      use-comments:
        description: 'Show templates as comments'
        required: true
        type: choice
        options: [ 'True', 'False' ]
        default: 'False'

jobs:
  create-localization-request:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          fetch-depth: 0
          ref: ${{ github.ref }}

      - name: Run Python Action from external repo
        id: run_action
        uses: Knutschbert/create-localization-issue@v0
        with:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          # base-dir: ""
          # base-file: ""
          branch: ${{ github.ref }}
          commit: ${{ github.event.inputs.commit }}
          # maintainers: ""
          template: ${{ github.event.inputs.template }}
          disable-mentions: ${{ github.event.inputs.disable-mentions }}
          js-patch: ${{ github.event.inputs.js-patch }}
          use-comments: ${{ github.event.inputs.use-comments }}
```
</details>

---

> [!NOTE]
> _If you prefer to handle the issue/comment creation yourself, use the action in `.github/actions/docker-action-folder`_

## Inputs

Default input parameters:
| input            | default                         | description                                                                        |
|------------------|---------------------------------|------------------------------------------------------------------------------------|
| **base-dir**         | assets/base/assets/localization | Directory containing localization files                                            |
| **base-file**        | en.json                         | Native translation file                                                            |
| **branch**           | main                            | Branch to operate on                                                               |
| **commit**           | HEAD^                           | Old commit to check against. Defaults to last                                      |
| **maintainers**      | localization_maintainers.json   | Path to maintainers JSON file                                                      |
| **template**         | /scripts/template.yml           | Path to YAML markdown template.  Defaults to the script in the action repo         |
| **disable-mentions** | False                           | Output mentions as text (dry-run)                                                  |
| **js-patch**         | False                           | Use diff output for translator templates                                           |
| **use-comments**     | False                           | Show language templates as comments. if False, templates will appear in issue body |


## Notes
- When working with many or large localization files, `use-comments` option might be needed (due to length limit of the issue body)
- Small flags next to maintainer names link to the corresponting comment/section