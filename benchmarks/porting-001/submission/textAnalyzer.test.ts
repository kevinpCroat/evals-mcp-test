/**
 * Comprehensive test suite for textAnalyzer module.
 * This is a port of the Python test suite to TypeScript/Jest.
 */

import {
  TextAnalyzer,
  tokenize,
  charFrequencyAnalysis,
  findPalindromes,
  groupByLength,
  calculateReadingMetrics,
  extractAcronyms,
  titleCaseSpecial,
  removeDuplicateWords
} from './textAnalyzer';

describe('TextAnalyzer', () => {
  describe('initialization', () => {
    test('initializes with text', () => {
      const text = "Hello world! This is a test.";
      const analyzer = new TextAnalyzer(text);
      expect(analyzer.wordCount()).toBeGreaterThan(0);
    });
  });

  describe('wordCount', () => {
    test('counts words correctly', () => {
      const analyzer = new TextAnalyzer("The quick brown fox jumps over the lazy dog");
      expect(analyzer.wordCount()).toBe(9);
    });

    test('returns 0 for empty text', () => {
      const analyzer = new TextAnalyzer("");
      expect(analyzer.wordCount()).toBe(0);
    });
  });

  describe('uniqueWords', () => {
    test('extracts unique words', () => {
      const analyzer = new TextAnalyzer("the cat and the dog");
      const unique = analyzer.uniqueWords();
      expect(unique).toEqual(new Set(["the", "cat", "and", "dog"]));
    });
  });

  describe('wordFrequency', () => {
    test('counts word frequencies', () => {
      const analyzer = new TextAnalyzer("the cat and the dog and the bird");
      const freq = analyzer.wordFrequency();
      expect(freq["the"]).toBe(3);
      expect(freq["and"]).toBe(2);
      expect(freq["cat"]).toBe(1);
    });
  });

  describe('mostCommonWords', () => {
    test('returns most common words', () => {
      const analyzer = new TextAnalyzer("a b c a b a");
      const common = analyzer.mostCommonWords(2);
      expect(common[0]).toEqual(["a", 3]);
      expect(common[1]).toEqual(["b", 2]);
    });
  });

  describe('averageWordLength', () => {
    test('calculates average word length', () => {
      const analyzer = new TextAnalyzer("cat dog bird");  // lengths: 3, 3, 4
      const avg = analyzer.averageWordLength();
      expect(Math.abs(avg - 3.333)).toBeLessThan(0.01);
    });

    test('returns 0 for empty text', () => {
      const analyzer = new TextAnalyzer("");
      expect(analyzer.averageWordLength()).toBe(0.0);
    });
  });

  describe('longestWords', () => {
    test('returns longest words', () => {
      const analyzer = new TextAnalyzer("a bb ccc dddd eeeee");
      const longest = analyzer.longestWords(3);
      expect(longest).toEqual(["eeeee", "dddd", "ccc"]);
    });
  });

  describe('punctuation handling', () => {
    test('removes punctuation properly', () => {
      const analyzer = new TextAnalyzer("Hello, world! How are you?");
      const words = analyzer.uniqueWords();
      expect(words.has("hello")).toBe(true);
      expect(words.has("world")).toBe(true);
      expect(words.has(",")).toBe(false);
    });
  });
});

describe('tokenize', () => {
  test('tokenizes basic text', () => {
    const tokens = tokenize("Hello world test");
    expect(tokens).toEqual(["hello", "world", "test"]);
  });

  test('removes punctuation', () => {
    const tokens = tokenize("Hello, world! How are you?");
    expect(tokens).toEqual(["hello", "world", "how", "are", "you"]);
  });

  test('preserves case when specified', () => {
    const tokens = tokenize("Hello World", false);
    expect(tokens).toEqual(["Hello", "World"]);
  });

  test('handles empty string', () => {
    const tokens = tokenize("");
    expect(tokens).toEqual([]);
  });
});

describe('charFrequencyAnalysis', () => {
  test('analyzes character frequency', () => {
    const freq = charFrequencyAnalysis("hello");
    expect(freq).toEqual({ h: 1, e: 1, l: 2, o: 1 });
  });

  test('ignores case by default', () => {
    const freq = charFrequencyAnalysis("AaBb", true);
    expect(freq).toEqual({ a: 2, b: 2 });
  });

  test('preserves case when specified', () => {
    const freq = charFrequencyAnalysis("AaBb", false);
    expect(freq).toEqual({ A: 1, a: 1, B: 1, b: 1 });
  });

  test('filters whitespace', () => {
    const freq = charFrequencyAnalysis("a b c");
    expect(freq[" "]).toBeUndefined();
    expect(freq).toEqual({ a: 1, b: 1, c: 1 });
  });
});

describe('findPalindromes', () => {
  test('finds basic palindromes', () => {
    const words = ["racecar", "hello", "level", "world"];
    const palindromes = findPalindromes(words);
    expect(new Set(palindromes)).toEqual(new Set(["racecar", "level"]));
  });

  test('respects minimum length', () => {
    const words = ["a", "aa", "aba", "abba"];
    const palindromes = findPalindromes(words, 3);
    expect(new Set(palindromes)).toEqual(new Set(["aba", "abba"]));
  });

  test('is case-insensitive', () => {
    const words = ["Racecar", "Level"];
    const palindromes = findPalindromes(words);
    expect(palindromes.length).toBe(2);
  });

  test('handles empty list', () => {
    const palindromes = findPalindromes([]);
    expect(palindromes).toEqual([]);
  });

  test('deduplicates results', () => {
    const words = ["level", "level", "kayak", "kayak"];
    const palindromes = findPalindromes(words);
    expect(palindromes.length).toBe(2);
  });
});

describe('groupByLength', () => {
  test('groups words by length', () => {
    const words = ["a", "bb", "ccc", "dd", "e"];
    const grouped = groupByLength(words);
    expect(grouped[1]).toEqual(["a", "e"]);
    expect(grouped[2]).toEqual(["bb", "dd"]);
    expect(grouped[3]).toEqual(["ccc"]);
  });

  test('handles empty list', () => {
    const grouped = groupByLength([]);
    expect(grouped).toEqual({});
  });

  test('preserves word order within groups', () => {
    const words = ["cat", "dog", "ant", "bee"];
    const grouped = groupByLength(words);
    expect(grouped[3]).toEqual(["cat", "dog", "ant", "bee"]);
  });
});

describe('calculateReadingMetrics', () => {
  test('calculates basic metrics', () => {
    const text = "Hello world. This is a test.";
    const metrics = calculateReadingMetrics(text);
    expect(metrics.sentence_count).toBe(2);
    expect(metrics.word_count).toBe(6);
    expect(metrics.character_count).toBe(text.length);
  });

  test('calculates average sentence length', () => {
    const text = "One two three. Four five six.";
    const metrics = calculateReadingMetrics(text);
    expect(metrics.avg_sentence_length).toBe(3.0);
  });

  test('handles empty text', () => {
    const metrics = calculateReadingMetrics("");
    expect(metrics.sentence_count).toBe(0);
    expect(metrics.word_count).toBe(0);
  });

  test('handles multiple punctuation types', () => {
    const text = "Question? Answer! Statement.";
    const metrics = calculateReadingMetrics(text);
    expect(metrics.sentence_count).toBe(3);
  });
});

describe('extractAcronyms', () => {
  test('extracts basic acronyms', () => {
    const text = "The FBI and CIA work together. USA is great.";
    const acronyms = extractAcronyms(text);
    expect(new Set(acronyms)).toEqual(new Set(["FBI", "CIA", "USA"]));
  });

  test('returns sorted acronyms', () => {
    const text = "USA FBI CIA";
    const acronyms = extractAcronyms(text);
    expect(acronyms).toEqual(["CIA", "FBI", "USA"]);
  });

  test('excludes single letters', () => {
    const text = "I love the FBI";
    const acronyms = extractAcronyms(text);
    expect(acronyms).not.toContain("I");
    expect(acronyms).toContain("FBI");
  });

  test('handles text with no acronyms', () => {
    const text = "Hello world this is a test";
    const acronyms = extractAcronyms(text);
    expect(acronyms).toEqual([]);
  });
});

describe('titleCaseSpecial', () => {
  test('converts to basic title case', () => {
    const result = titleCaseSpecial("the quick brown fox");
    expect(result).toBe("The Quick Brown Fox");
  });

  test('keeps minor words lowercase', () => {
    const result = titleCaseSpecial("the lord of the rings");
    expect(result).toBe("The Lord of the Rings");
  });

  test('capitalizes first and last words', () => {
    const result = titleCaseSpecial("a tale of two cities");
    expect(result).toBe("A Tale of Two Cities");
  });

  test('uses custom minor words', () => {
    const result = titleCaseSpecial("hello from the world", new Set(["from"]));
    expect(result).toBe("Hello from The World");
  });

  test('handles empty string', () => {
    const result = titleCaseSpecial("");
    expect(result).toBe("");
  });

  test('handles single word', () => {
    const result = titleCaseSpecial("hello");
    expect(result).toBe("Hello");
  });
});

describe('removeDuplicateWords', () => {
  test('removes duplicates preserving order', () => {
    const text = "the cat and the dog and the bird";
    const result = removeDuplicateWords(text, true);
    expect(result).toBe("the cat and dog bird");
  });

  test('removes duplicates with sorting', () => {
    const text = "zebra apple banana apple";
    const result = removeDuplicateWords(text, false);
    expect(result).toBe("apple banana zebra");
  });

  test('is case-insensitive', () => {
    const text = "Hello world hello WORLD";
    const result = removeDuplicateWords(text, true);
    const words = result.split(' ');
    expect(words.length).toBe(2);
  });

  test('handles empty string', () => {
    const result = removeDuplicateWords("");
    expect(result).toBe("");
  });

  test('handles text with no duplicates', () => {
    const text = "one two three";
    const result = removeDuplicateWords(text);
    expect(result).toBe("one two three");
  });
});
