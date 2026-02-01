/**
 * Text Analysis Utility Module
 *
 * A comprehensive text processing library with various analysis and transformation
 * functions. This is a TypeScript port of the Python text_analyzer module.
 */

/**
 * Analyzes text content with various metrics and transformations.
 */
export class TextAnalyzer {
  private text: string;
  private words: string[];

  /**
   * Initialize the analyzer with text content.
   * @param text - The text to analyze
   */
  constructor(text: string) {
    this.text = text;
    this.words = this.extractWords(text);
  }

  /**
   * Extract words from text, removing punctuation.
   */
  private extractWords(text: string): string[] {
    const matches = text.match(/\b\w+\b/g);
    return matches ? matches.map(word => word.toLowerCase()) : [];
  }

  /**
   * Return the total number of words.
   */
  wordCount(): number {
    return this.words.length;
  }

  /**
   * Return a set of unique words.
   */
  uniqueWords(): Set<string> {
    return new Set(this.words);
  }

  /**
   * Return a map of word frequencies.
   * @returns Map of words to their occurrence counts
   */
  wordFrequency(): Record<string, number> {
    const frequency: Record<string, number> = {};
    for (const word of this.words) {
      frequency[word] = (frequency[word] || 0) + 1;
    }
    return frequency;
  }

  /**
   * Return the n most common words with their frequencies.
   * @param n - Number of top words to return
   * @returns Array of [word, count] tuples sorted by frequency
   */
  mostCommonWords(n: number = 5): Array<[string, number]> {
    const frequency = this.wordFrequency();
    const entries = Object.entries(frequency);
    entries.sort((a, b) => b[1] - a[1]);
    return entries.slice(0, n) as Array<[string, number]>;
  }

  /**
   * Calculate the average length of words.
   */
  averageWordLength(): number {
    if (this.words.length === 0) {
      return 0.0;
    }
    const totalLength = this.words.reduce((sum, word) => sum + word.length, 0);
    return totalLength / this.words.length;
  }

  /**
   * Return the n longest words.
   * @param n - Number of longest words to return
   * @returns Array of longest words, sorted by length descending
   */
  longestWords(n: number = 3): string[] {
    const uniqueWords = Array.from(new Set(this.words));
    uniqueWords.sort((a, b) => b.length - a.length);
    return uniqueWords.slice(0, n);
  }
}

/**
 * Tokenize text into words.
 * @param text - Input text to tokenize
 * @param lowercase - Whether to convert to lowercase
 * @returns Array of tokens
 */
export function tokenize(text: string, lowercase: boolean = true): string[] {
  const matches = text.match(/\b\w+\b/g);
  if (!matches) {
    return [];
  }
  return lowercase ? matches.map(w => w.toLowerCase()) : matches;
}

/**
 * Analyze character frequency in text.
 * @param text - Text to analyze
 * @param ignoreCase - Whether to treat upper and lower case as same
 * @returns Object mapping characters to their counts
 */
export function charFrequencyAnalysis(
  text: string,
  ignoreCase: boolean = true
): Record<string, number> {
  const processedText = ignoreCase ? text.toLowerCase() : text;
  const chars = processedText.split('').filter(c => /[a-zA-Z0-9]/.test(c));

  const frequency: Record<string, number> = {};
  for (const char of chars) {
    frequency[char] = (frequency[char] || 0) + 1;
  }
  return frequency;
}

/**
 * Find palindrome words in a list.
 * @param words - List of words to check
 * @param minLength - Minimum length for palindromes
 * @returns Array of palindrome words (deduplicated and sorted)
 */
export function findPalindromes(
  words: string[],
  minLength: number = 3
): string[] {
  const palindromes = words.filter(word => {
    const lower = word.toLowerCase();
    return lower.length >= minLength && lower === lower.split('').reverse().join('');
  });

  return Array.from(new Set(palindromes)).sort();
}

/**
 * Group words by their length.
 * @param words - List of words to group
 * @returns Object mapping lengths to arrays of words
 */
export function groupByLength(words: string[]): Record<number, string[]> {
  const grouped: Record<number, string[]> = {};

  for (const word of words) {
    const len = word.length;
    if (!grouped[len]) {
      grouped[len] = [];
    }
    grouped[len].push(word);
  }

  return grouped;
}

/**
 * Calculate various reading metrics for text.
 * @param text - Text to analyze
 * @returns Object with metrics including sentence count, avg sentence length, etc.
 */
export function calculateReadingMetrics(text: string): {
  sentence_count: number;
  word_count: number;
  character_count: number;
  avg_sentence_length: number;
  avg_word_length: number;
} {
  // Split into sentences (simple approach)
  const sentences = text
    .split(/[.!?]+/)
    .map(s => s.trim())
    .filter(s => s.length > 0);

  const words = tokenize(text);

  return {
    sentence_count: sentences.length,
    word_count: words.length,
    character_count: text.length,
    avg_sentence_length: sentences.length > 0 ? words.length / sentences.length : 0,
    avg_word_length: words.length > 0 ? words.reduce((sum, w) => sum + w.length, 0) / words.length : 0
  };
}

/**
 * Extract potential acronyms (all-caps words of 2+ letters).
 * @param text - Text to scan for acronyms
 * @returns Array of unique acronyms found, sorted alphabetically
 */
export function extractAcronyms(text: string): string[] {
  const matches = text.match(/\b[A-Z]{2,}\b/g);
  if (!matches) {
    return [];
  }
  return Array.from(new Set(matches)).sort();
}

/**
 * Convert text to title case with special rules for minor words.
 *
 * Minor words (articles, conjunctions, prepositions) are lowercase
 * unless they're the first or last word.
 *
 * @param text - Text to convert
 * @param minorWords - Set of words to keep lowercase
 * @returns Title-cased string
 */
export function titleCaseSpecial(
  text: string,
  minorWords?: Set<string>
): string {
  const defaultMinorWords = new Set([
    'a', 'an', 'the', 'and', 'but', 'or', 'for', 'nor',
    'on', 'at', 'to', 'from', 'by', 'in', 'of'
  ]);

  const minor = minorWords || defaultMinorWords;
  const words = text.split(' ');

  if (words.length === 0) {
    return text;
  }

  // First word is always capitalized
  const result: string[] = [capitalize(words[0])];

  // Middle words
  for (let i = 1; i < words.length - 1; i++) {
    const word = words[i];
    if (minor.has(word.toLowerCase())) {
      result.push(word.toLowerCase());
    } else {
      result.push(capitalize(word));
    }
  }

  // Last word is always capitalized (if more than one word)
  if (words.length > 1) {
    result.push(capitalize(words[words.length - 1]));
  }

  return result.join(' ');
}

/**
 * Helper function to capitalize a word.
 */
function capitalize(word: string): string {
  if (!word) return word;
  return word.charAt(0).toUpperCase() + word.slice(1).toLowerCase();
}

/**
 * Remove duplicate words from text.
 * @param text - Input text
 * @param preserveOrder - If true, preserve first occurrence order;
 *                        if false, sort alphabetically
 * @returns Text with duplicates removed
 */
export function removeDuplicateWords(
  text: string,
  preserveOrder: boolean = true
): string {
  const words = text.split(' ');

  if (preserveOrder) {
    const seen = new Set<string>();
    const uniqueWords: string[] = [];

    for (const word of words) {
      const wordLower = word.toLowerCase();
      if (!seen.has(wordLower)) {
        seen.add(wordLower);
        uniqueWords.push(word);
      }
    }
    return uniqueWords.join(' ');
  } else {
    const uniqueWords = Array.from(new Set(words.map(w => w.toLowerCase())));
    uniqueWords.sort();
    return uniqueWords.join(' ');
  }
}
