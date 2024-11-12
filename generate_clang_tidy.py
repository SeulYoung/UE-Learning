import re

FILE_NAME = "checks_list.html"
ALIASES_START = "check-aliases"
MATCH_PATTERN = r'<tr class="row-[a-z]+">.+<span class="doc">(.+)</span></a></p></td>'

EXCLUDE_CHECKS = ["abseil-*",
                  "android-*",
                  "boost-*",
                  "objc-*",
                  "cert-err33-c",
                  "modernize-use-trailing-return-type",
                  "modernize-use-designated-initializers",
                  "modernize-use-nodiscard",
                  "modernize-avoid-c-arrays",
                  "cppcoreguidelines-owning-memory",
                  "cppcoreguidelines-avoid-do-while",
                  "cppcoreguidelines-init-variables",
                  "cppcoreguidelines-avoid-non-const-global-variables",
                  "cppcoreguidelines-pro-bounds-array-to-pointer-decay",
                  "cppcoreguidelines-pro-bounds-constant-array-index",
                  "cppcoreguidelines-avoid-const-or-ref-data-members",
                  "bugprone-easily-swappable-parameters",
                  "readability-convert-member-functions-to-static", # Clion
                  "readability-function-cognitive-complexity",
                  "readability-math-missing-parentheses",
                  "readability-uppercase-literal-suffix",
                  "readability-identifier-length",
                  "readability-implicit-bool-conversion",
                  "readability-isolate-declaration",
                  "readability-magic-numbers",
                  "llvmlibc-implementation-in-namespace",
                  "llvmlibc-callee-namespace",
                  "llvm-namespace-comment",
                  "llvmlibc-inline-function-decl",
                  "llvm-include-order",
                  "altera-id-dependent-backward-branch",
                  "altera-struct-pack-align",
                  "altera-unroll-loops",
                  "misc-non-private-member-variables-in-classes",
                  "misc-use-anonymous-namespace",
                  "misc-unused-parameters",
                  "misc-no-recursion",
                  "fuchsia-overloaded-operator",
                  "fuchsia-statically-constructed-objects",
                  "fuchsia-default-arguments-declarations",
                  "fuchsia-default-arguments-calls"]


def generate_clion(checks):
    output = "*"
    for check in checks:
        output += ","
        output += "-" + check

    with open("output.txt", "w") as wf:
        wf.write(output)


def generate_rider(checks):
    pass


if __name__ == '__main__':
    with open(FILE_NAME, "r", encoding="utf8") as f:
        check_with_alias = [c for c in EXCLUDE_CHECKS]
        pattern = re.compile(MATCH_PATTERN)

        aliases_start = False
        for line in f.readlines():
            if ALIASES_START in line:
                aliases_start = True

            if not aliases_start:
                continue

            matches = pattern.search(line)
            if matches:
                check_with_alias.append(matches.group(1))

        generate_clion(check_with_alias)
        generate_rider(check_with_alias)
