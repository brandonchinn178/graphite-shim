# graphite-shim

At Snowflake, I started using graphite and really liked the UX. However, it's GitHub-specific and forces you into the graphite ecosystem, which is less ideal for open source and personal projects. `graphite-shim` is a translation layer that proxies for `gt` in Graphite projects, or provides a minimal implementation for non-Graphite projects.

## Requirements

* At least Python 3.12 installed

## Installation

After cloning this repo somewhere, add the following to `bashrc`/`zshrc`:

```shell
alias gt=/path/to/graphite-shim/entrypoint.sh
```
