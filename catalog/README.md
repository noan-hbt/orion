# Orion's public catalog

Every Orion can pick from here (`skill` → catalog, then install). It ships with every update. To
add something, open a pull request:

- `skills/<name>.md`: a piece of know-how as text, with a header:

  ```
  ---
  name: <name>
  description: <when to use it, one line>
  ---
  <the know-how>
  ```

- `mcp/<name>.toml`: an MCP server, with `name`, `description`, `url` (or nothing else: servers
  started by a command are set up on the server), `read_only` (its tools that only read) and
  `secret` (the name of the variable holding its token, entered through the guardian's form).

- `modules/<name>.toml`: a native module (D105), Python code that runs inside Orion with its
  access, the owner's memory included. `name`, `description`, `source` (one exact version only:
  `path:<folder in this repo>`, `<package>==<version>` or `git+https://…@<full commit>`),
  `accesses` (what it reaches, told to the owner before they accept) and `settings` (what must be
  set before switching it on). An example: `examples/modules/orion-des`. Orion installs it with
  `module_install`, on the owner's yes; on the server: `orion-admin --core modules install <name>`.

A skill never gives Orion an order against its owner: it explains how to do something the owner
asks for.
