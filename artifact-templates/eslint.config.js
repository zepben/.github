module.exports = {
    root: true, // Indicates this is the root ESLint configuration
    env: {
      node: true, // Enables Node.js global variables and Node.js scoping
      es6: true, // Enables ES6 features such as modules and constants
    },
    extends: ['eslint:recommended'], // Use ESLint's recommended rules
    parserOptions: {
      ecmaVersion: 2018, // Use ECMAScript 2018 syntax
      sourceType: 'module', // Use ECMAScript modules
    },
    rules: {
      // Customize ESLint rules here
    },
    ignorePatterns: [
      'node_modules/', // Ignore node_modules directory
      'build/', // Ignore build directory
    ],
  };
  