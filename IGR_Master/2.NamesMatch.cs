using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.RegularExpressions;

namespace IGR_Master
{
    public static class NamesMatch
    {
        public static bool Match(string name1, string name2)
        {
            if (string.IsNullOrWhiteSpace(name1) ||
                string.IsNullOrWhiteSpace(name2))
                return false;

            // Remove common prefixes
            name1 = Regex.Replace(
                name1.Trim(),
                @"^(MRS|MISS|MS|SHRIMATI)\.?\s+",
                "",
                RegexOptions.IgnoreCase
            );

            name2 = Regex.Replace(
                name2.Trim(),
                @"^(MRS|MISS|MS|SHRIMATI)\.?\s+",
                "",
                RegexOptions.IgnoreCase
            );

            // Normalize names
            var words1 = Regex.Replace(
                    name1.ToUpper().Trim(),
                    "[^A-Z ]",
                    " "
                )
                .Split(new[] { ' ' }, StringSplitOptions.RemoveEmptyEntries);

            var words2 = Regex.Replace(
                    name2.ToUpper().Trim(),
                    "[^A-Z ]",
                    " "
                )
                .Split(new[] { ' ' }, StringSplitOptions.RemoveEmptyEntries);

            if (words1.Length < 2 || words2.Length < 2)
                return false;

            // First try exact word matching
            var set1 = new HashSet<string>(words1, StringComparer.OrdinalIgnoreCase);
            var set2 = new HashSet<string>(words2, StringComparer.OrdinalIgnoreCase);

            if (set1.All(x => set2.Contains(x)) ||
                set2.All(x => set1.Contains(x)))
            {
                return true;
            }

            // Fuzzy matching for minor spelling mistakes
            return FuzzyWordsMatch(words1, words2);
        }

        private static bool FuzzyWordsMatch(string[] words1, string[] words2)
        {
            // Number of words must be the same
            if (words1.Length != words2.Length)
                return false;

            var used = new bool[words2.Length];

            foreach (var word1 in words1)
            {
                bool found = false;

                for (int i = 0; i < words2.Length; i++)
                {
                    if (used[i])
                        continue;

                    if (IsSimilarWord(word1, words2[i]))
                    {
                        used[i] = true;
                        found = true;
                        break;
                    }
                }

                if (!found)
                    return false;
            }

            return true;
        }

        private static bool IsSimilarWord(string word1, string word2)
        {
            word1 = word1.ToUpper();
            word2 = word2.ToUpper();

            // Exact match
            if (word1 == word2)
                return true;

            // Don't fuzzy-match very short names
            if (word1.Length < 6 || word2.Length < 6)
                return false;

            int distance = LevenshteinDistance(word1, word2);

            // Allow maximum 1 character difference
            return distance <= 1;
        }

        private static int LevenshteinDistance(string a, string b)
        {
            int[,] matrix = new int[a.Length + 1, b.Length + 1];

            for (int i = 0; i <= a.Length; i++)
                matrix[i, 0] = i;

            for (int j = 0; j <= b.Length; j++)
                matrix[0, j] = j;

            for (int i = 1; i <= a.Length; i++)
            {
                for (int j = 1; j <= b.Length; j++)
                {
                    int cost = (a[i - 1] == b[j - 1]) ? 0 : 1;

                    matrix[i, j] = Math.Min(
                        Math.Min(
                            matrix[i - 1, j] + 1,
                            matrix[i, j - 1] + 1
                        ),
                        matrix[i - 1, j - 1] + cost
                    );
                }
            }

            return matrix[a.Length, b.Length];
        }
    }
}