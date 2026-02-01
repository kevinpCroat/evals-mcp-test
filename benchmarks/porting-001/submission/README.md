# Text Analyzer - TypeScript Implementation

This is a TypeScript port of the Python text analysis library.

## Installation

```bash
npm install
```

## Running Tests

```bash
npm test
```

## Running Linter

```bash
npm run lint
```

## Building

```bash
npm run build
```

## Features

All functions from the Python version have been ported:

- **TextAnalyzer class**: Object-oriented text analysis
- **tokenize()**: Word tokenization
- **charFrequencyAnalysis()**: Character frequency counting
- **findPalindromes()**: Palindrome detection
- **groupByLength()**: Group words by length
- **calculateReadingMetrics()**: Reading statistics
- **extractAcronyms()**: Acronym extraction
- **titleCaseSpecial()**: Smart title case conversion
- **removeDuplicateWords()**: Duplicate removal

## Implementation Notes

This port uses idiomatic TypeScript/JavaScript patterns:

- Classes with proper encapsulation
- Array methods (map, filter, reduce) instead of list comprehensions
- Objects and Maps for dictionaries
- Set for unique collections
- Proper type annotations
- Modern ES6+ features (arrow functions, destructuring, etc.)
