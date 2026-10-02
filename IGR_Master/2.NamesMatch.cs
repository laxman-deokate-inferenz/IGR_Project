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
            
            
            
            
            var words1 = new HashSet<string>(
                Regex.Replace(
                    name1.ToUpper().Trim(),
                    "[^A-Z ]",
                    " "
                ).Split(
                    new[] { ' ' },
                    StringSplitOptions.RemoveEmptyEntries
                ),
                StringComparer.OrdinalIgnoreCase
            );

            var words2 = new HashSet<string>(
                Regex.Replace(
                    name2.ToUpper().Trim(),
                    "[^A-Z ]",
                    " "
                ).Split(
                    new[] { ' ' },
                    StringSplitOptions.RemoveEmptyEntries
                ),
                StringComparer.OrdinalIgnoreCase
            );

            if (words1.Count < 2 || words2.Count < 2)
                return false;

            return words1.All(x => words2.Contains(x)) ||
                   words2.All(x => words1.Contains(x));
        }
    }
}