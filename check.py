import argparse
import polib
import language_tool_python
from colorama import Fore, Style
import os
import json
from jsonschema import validate
import jsonschema_default

schema = {
    "type": "object",
    "properties": {
        "enableCorrections": {"type": "boolean", "default": False},
        "checkSourceString": {"type": "boolean", "default": True},
        "checkTranslationString": {"type": "boolean", "default": False},
        "customDictionary": {
            "type": "array",
            "items": {"type": "string"},
            "default": [],
        },
        "disabledRules": {"type": "array", "items": {"type": "string"}, "default": []},
    },
    "required": [],
}


class poChecker:
    def __init__(
        self,
        path,
        language="en-US",
        correct=False,
        check_source=True,
        check_translation=False,
        dict=[],
        disabledRules=[],
        verbose=False,
    ):
        self.pofile = polib.pofile(path)
        self.tool = language_tool_python.LanguageTool(
            language,
            config={
                "cacheSize": 1000,
                "pipelineCaching": True,
                "maxSpellingSuggestions": 1,
                "disabledRuleIds": ",".join(disabledRules),
            },
        )
        self.correct = correct
        self.check_source = check_source
        self.check_translation = check_translation
        self.dict = dict
        self.verbose = verbose

    def process(self):
        for entry in self.pofile:
            if self.check_source:
                issues = self.tool.check(entry.msgid)
                if len(issues) > 0:
                    for issue in issues:
                        if self.isIssueValid(issue):
                            self.outputIssue(issue)

            if self.check_translation and entry.msgstr:
                issues = self.tool.check(entry.msgstr)
                if len(issues) > 0:
                    for issue in issues:
                        if self.isIssueValid(issue):
                            self.outputIssue(issue)

        self.tool.close()

    def isIssueValid(self, issue):
        context = issue.context[
            issue.offsetInContext : issue.offsetInContext + issue.errorLength
        ]

        if context in self.dict:
            return False
        else:
            return True

    def outputIssue(self, issue):
        offset = " " * issue.offsetInContext
        pointer = "^" * issue.errorLength
        print(Fore.RED + f"{issue.message.strip()}")
        print(Fore.YELLOW + f"{issue.context.strip()}")
        print(f"{offset}{pointer}")

        if issue.replacements and issue.replacements[0]:
            print(Fore.GREEN + f"{offset}{issue.replacements[0]}")

        if self.verbose:
            print(Fore.WHITE + f"Triggered rule ID: {issue.ruleId}")

        print(Style.RESET_ALL)


def main():
    # Create argument parser
    parser = argparse.ArgumentParser(description="Process a .po file path")
    parser.add_argument("--path", type=str, help="Path to the .po file")
    parser.add_argument(
        "--language",
        type=str,
        default="en-US",
        help="The language of the input file (Examples: en-US, en, es, ca-ES)",
    )
    parser.add_argument(
        "--config",
        type=str,
        default="potLanguageChecker.json",
        help="The PotLangueChecker config file to read.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Displays additional info such as what rule ID was striggered",
    )

    args = parser.parse_args()

    if not os.path.exists(args.config):
        print(Fore.RED + f"Config file {args.config} does not exist")
        exit(1)

    with open(args.config, "r") as f:
        config = json.load(f)

    validate(instance=config, schema=schema)
    default_config = jsonschema_default.create_from(schema)
    config = {**default_config, **config}

    checker = poChecker(
        args.path,
        language=args.language,
        correct=config["enableCorrections"],
        check_source=config["checkSourceString"],
        check_translation=config["checkTranslationString"],
        dict=config["customDictionary"],
        verbose=args.verbose,
    )

    checker.process()


if __name__ == "__main__":
    main()
