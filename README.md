# create-localization-issue

A Github Action to generate Issues when base localization file is updated.
Generated Issues feature translator @ mentions as well as JSON templates which translators can directly use.

[Examples of generated issues](https://github.com/Knutschbert/create-localization-issue/issues?q=label%3AExample%20)


This action assumes that localization files are simple JSON files with a dictionary containing string key-value pairs (`Dict[str,str]`).

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

1. Create a file containing github user tags of translators (default: `localization_maintainers.json`):
    ```json
    {
        "de.json": ["@knutschbert"],
        "ua.json": ["@knutschbert"]
    }
    ```

2. Adjust the workflow below to your needs
- <details>
  <summary><b>Example workflow</b></summary>


  ```yaml
  name: Create Localization Help Issue

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
        labels:
          description: 'Issue, labels'
          required: false
          default: 'localization, automated, help wanted'

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
            # base-dir: "assets/base/assets/localization"
            # base-file: "en.json"
            branch: ${{ github.ref }}
            commit: ${{ github.event.inputs.commit }}
            # maintainers: "localization_maintainers.json"
            template: ${{ github.event.inputs.template }}
            disable-mentions: ${{ github.event.inputs.disable-mentions }}
            js-patch: ${{ github.event.inputs.js-patch }}
            use-comments: ${{ github.event.inputs.use-comments }}
            labels: ${{ github.event.inputs.labels }}
  ```
</details>

---

> [!Important]
> When dealing with a large filebase or many keys, consider turning `use-comments` on

> [!NOTE]
> _If you prefer to handle the issue/comment creation yourself, use this action to generate issue body and comments:
> `.github/actions/docker-action-folder`_

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
| **labels**     | localization, automated, help wanted    | Comma separated list of issue labels |


## Notes
- When working with many or large localization files, `use-comments` option might be needed (due to length limit of the issue body)
- Small flags next to maintainer names link to the corresponting comment/section
- 🪜 takes you back to the top
- Flag icon and descriptive language names require [ISO 639](https://en.wikipedia.org/wiki/List_of_ISO_639_language_codes) naming
  - both `alpha-2` _(de)_ and `alpha-3` _(deu)_ names are supported
  - if it fails, treats name as country code and tries `alpha-3` for language (e.g. `ua.json` and `uk.json` will both work)


## Translator JSON templates

<details>
<summary>Example issue comment (generated with use-comments=True)</summary>

<a name="ua.json"></a>
## <img  alt="Ukrainian" src="https://upload.wikimedia.org/wikipedia/commons/thumb/4/49/Flag_of_Ukraine.svg/60px-Flag_of_Ukraine.svg.png"> Ukrainian (ua.json)

[✏️ Edit ua.json on Github](../edit/loc_wf/assets/base/assets/localization/ua.json)

<details>

<summary> JSON Template for <b>ua.json</b></summary>


```json
{
  "add_directory_to_scan_for_games_button_text": "Додати папку для скану ігор",
  "add_game_by_game_directory": "Додати папку з грою",
  "cleaning_up_temp_files_step_text": "Видаляю тимчасові файли",
  "close_button_text": "Закрити",
  "discord_button_text": "Discord",
  "docs_button_text": "Документація",
  "downloading_ue4ss_zip_step_text": "UE4SS zip завантажується",
  "enable_pre_releases_text_label": "Активувати пре-релізи",
  "game_directory_text_label": "Папка з грою:",
  "github_button_text": "Github",
  "header_text": "Встановлювач UE4SS",
  "install_button_text": "Встановити",
  "install_developer_version_text_label": "Завантажити версію для розробників (якщо це можливо)",
  "install_failed_message_text": "Інсталяція не вдалася",
  "install_from_zip_button_text": "Встановити з zip",
  "install_portable_version_text_label": "Завантажити портативну версію (якщо це можливо)",
  "install_succeeded_message_text": "Інсталяція пройшла успішно",
  "installing_from_zip_ue4ss_task_text": "Встановлює UE4SS з zip файлу",
//⚠️  "installing_ue4ss_step_text": "Installing UE4SS",
//⚠️  "installing_ue4ss_task_text": "Installing UE4SS",
//⚠️  "keep_mods_and_settings_text_label": "Keep user files on uninstall/reinstall",
//⚠️  "open_game_exe_directory": "Open game exe directory",
//  "open_game_paks_directory": "Open game paks directory",
  "reinstall_button_text": "Перевстановити",
  "reinstalling_ue4ss_task_text": "Перевстановлює UE4SS",
  "sub_header_text": "Щоб встановити UE4SS, виберіть одну з ігор нижче або додайте гру вручну",
  "filter_ue4ss_version_hint": "Фільтр версії UE4SS тут...",
  "filter_ue4ss_file_hint": "Фільтр архівного файлу для встановлення...",
  "ue4ss_file_to_install_text_label": "Архів для встановлення:",
  "ue4ss_version_text_label": "Версія UE4SS:",
  "uninstall_button_text": "Видалити",
  "uninstall_failed_message_text": "Видалення не вдалося",
  "uninstall_succeeded_message_text": "Видалення пройшло успішно",
  "uninstalling_old_ue4ss_files_step_text": "Видалення старих файлів UE4SS",
  "uninstalling_ue4ss_task_text": "Видалення UE4SS",
//  "test_teststring22": "This key was changed again",
//  "test_teststring2": "This key was changed"
}

```

</details>

### Warnings

- ⚠️ **`installing_ue4ss_step_text`** is missing!

- ⚠️ **`installing_ue4ss_task_text`** is missing!

- ⚠️ **`keep_mods_and_settings_text_label`** is missing!

- ⚠️ **`open_game_exe_directory`** is missing!


## <a href="#top">🪜</a>
</details>

## Customization
You can customize issue/comment body by providing a custom template file in YAML format.

Original template is located at [`scripts/template.yml`](https://github.com/Knutschbert/create-localization-issue/blob/main/scripts/template.yml)