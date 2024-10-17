import hypothesis from 'eslint-config-hypothesis';
import jsxA11y from 'eslint-plugin-jsx-a11y';
import globals from 'globals';
import tseslint from 'typescript-eslint';

export default tseslint.config(
  {
    ignores: [
      '.tox/**/*',
      '.yalc/**/*',
      '.yarn/**/*',
      'build/**/*',
      '**/vendor/**/*.js',
      '**/coverage/**/*',
      'docs/_build/*',
      'via/static/js/**',
    ],
  },
  ...hypothesis,
  ...tseslint.configs.recommended,
  jsxA11y.flatConfigs.recommended,
  {
    rules: {
      'prefer-arrow-callback': 'error',
      'prefer-const': ['error', { destructuring: 'all' }],

      // Props are checked by TS.
      'react/prop-types': 'off',

      // Upgrade TS rules from warning to error.
      '@typescript-eslint/no-unused-vars': 'error',

      // Disable TS rules that we dislike.
      '@typescript-eslint/ban-ts-comment': 'off',
      '@typescript-eslint/no-empty-function': 'off',
      '@typescript-eslint/no-explicit-any': 'off',
      '@typescript-eslint/no-non-null-assertion': 'off',
      '@typescript-eslint/no-this-alias': 'off',

      // Enforce consistency in cases where TypeScript supports old and new
      // syntaxes for the same thing.
      //
      // - Require `<var> as <type>` for casts
      // - Require `import type` for type imports. The corresponding rule for
      //   exports is not enabled yet because that requires setting up type-aware
      //   linting.
      '@typescript-eslint/consistent-type-assertions': 'error',
      '@typescript-eslint/consistent-type-imports': 'error',
    },
  },

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
