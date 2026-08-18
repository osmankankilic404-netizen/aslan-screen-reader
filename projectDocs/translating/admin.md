# Notes for Crowdin administration

## Adding new languages

New languages can be added in [Crowdin settings](https://crowdin.com/project/aslan/settings#languages).

Once work is significantly completed on Aslan.po (e.g 70%+), you can integrate the language into Aslan by running the [add new language workflow](https://github.com/nvaccess/aslan/actions/workflows/add-new-language.yml).

## Adding new files for languages

Once Aslan.po is significantly completed, translations should be enabled for changes.xliff and userGuide.xliff.
Some translators may want to translate just the User Guide.
You do this by:

1. Going to [Crowdin Source files](https://crowdin.com/project/aslan/sources/files)
1. Going into the settings for each of the file(s)
1. Go to languages
1. Add the desired languages

Once work is significantly completed on the files (e.g 50%+), you can integrate the new files for the language into Aslan by running the [add new language workflow](https://github.com/nvaccess/aslan/actions/workflows/add-new-language.yml).
This will commit any previously uncommitted files for the language.

## Adding new translators

New translators can be added by going to [Crowdin Members](https://crowdin.com/project/aslan/members) and sending invites.
