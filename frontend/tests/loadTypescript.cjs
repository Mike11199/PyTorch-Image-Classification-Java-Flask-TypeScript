const fs = require('node:fs');
const path = require('node:path');
const Module = require('node:module');
const ts = require('typescript');
const cache = new Map();

/** Load pure TS modules in the built-in runner without a bundler subprocess. */
function loadTypescript(filename) {
  filename = path.resolve(filename);
  if (cache.has(filename)) return cache.get(filename).exports;
  const loaded = new Module(filename, module);
  cache.set(filename, loaded);
  loaded.require = (specifier) => specifier.startsWith('.')
    ? loadTypescript(path.resolve(path.dirname(filename), specifier + '.ts'))
    : require(specifier);
  const { outputText } = ts.transpileModule(fs.readFileSync(filename, 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020 },
  });
  loaded._compile(outputText, filename);
  return loaded.exports;
}

module.exports = { loadTypescript };
