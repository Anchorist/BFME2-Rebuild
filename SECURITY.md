# Security

Please report security problems privately, through GitHub: open the repository's **Security** tab and choose
**Report a vulnerability**. Do not open a public issue for them.

What counts here:

- a way for a pull request to run its own code with write access to the repository, or to read a secret;
- a way to make a check pass without the change being measured, or to change `main` without the checks;
- anything that exposes a credential or private data in the repository, its history or a check's output.

Disagreements about whether a function matches, a name or a file placement are not security problems: open an
ordinary issue with the evidence instead (see `CONTRIBUTING.md`).

The maintainer reads reports on GitHub and answers there. There is no bounty.
