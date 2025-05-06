import hypothesisBase from 'eslint-config-hypothesis/base';
import hypothesisJSX from 'eslint-config-hypothesis/jsx';
import hypothesisTS from 'eslint-config-hypothesis/ts';
import { defineConfig, globalIgnores } from 'eslint/config';
import globals from 'globals';

export default defineConfig(
  globalIgnores([
    '.tox/**/*',
    '.yalc/**/*',
    '.yarn/**/*',
    'build/**/*',
    '**/vendor/**/*.js',
    '**/coverage/**/*',
    'docs/_build/*',
    'via/static/js/**',
  ]),

  hypothesisBase,
  hypothesisJSX,
  hypothesisTS,

  // Icons
  {
    files: ['via/static/scripts/**/components/icons/*.tsx'],
    rules: {
      // preact uses kebab-cased SVG element attributes, which look like
      // unknown properties to `eslint-plugin-react` (React uses camelCase
      // for these properties)
      'react/no-unknown-property': 'off',
    },
  },

  // Additional rules that require type information. These can only be run
  // on files included in the TS project by tsconfig.json.
  {
    files: ['via/static/scripts/*.{js,ts,tsx}'],
    ignores: ['via/static/scripts/setup-tests.js', '**/test/*.js'],
    rules: {
      '@typescript-eslint/no-unnecessary-condition': 'error',
    },
    languageOptions: {
      parserOptions: {
        project: 'via/static/scripts/tsconfig.json',
      },
    },
  },

  // Code that runs in Node
  {
    files: ['*.js'],
    ignores: ['via/**'],
    languageOptions: {
      globals: {
        ...globals.node,
      },
    },
  },
);
