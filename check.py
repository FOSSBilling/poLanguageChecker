import argparse
import polib
import language_tool_python
from colorama import Fore, Style


class poChecker:
    def __init__(
        self,
        path,
        language="en-US",
        correct=False,
        check_source=True,
        check_translation=False,
        ignore="",
    ):
        self.pofile = polib.pofile(path)
        self.tool = language_tool_python.LanguageTool(language)
        self.corret = correct
        self.check_source = check_source
        self.check_translation = check_translation
        self.ignore = list(ignore.split(","))

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

    def isIssueValid(self, issue):
        context = issue.context[
            issue.offsetInContext : issue.offsetInContext + issue.errorLength
        ]

        if context in self.ignore:
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
        "--correct",
        action="store_true",
        help="If automated corrections should be enabled or disabled",
    )
    parser.add_argument(
        "--check-source",
        action="store_false",
        help="If translation sources (msid) should be checked",
    )
    parser.add_argument(
        "--check-translation",
        action="store_true",
        help="If the translation (msgstr) should be checked",
    )
    parser.add_argument(
        "--ignore",
        default="",
        help="A comma seperated list of ignore words",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Output ",
    )

    args = parser.parse_args()

    checker = poChecker(
        args.path,
        language=args.language,
        correct=args.correct,
        check_source=args.check_source,
        check_translation=args.check_translation,
        ignore=args.ignore,
    )

    checker.process()


if __name__ == "__main__":
    main()
