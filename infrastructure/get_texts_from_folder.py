import os


def get_texts_from_folder():
    """
    Get list of text files from the texts folder

    Returns:
        list: List of text filenames, or empty list if folder doesn't exist
    """
    # Get the base directory of the project (assumes this script is in a subfolder)
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    texts_folder = os.path.join(base_dir, 'content', 'texts')

    if not os.path.exists(texts_folder):
        return []

    # Common text file extensions
    texts_extensions = {
        # Common text and markup files
        '.txt', '.md', '.rst', '.csv', '.tsv', '.log', '.out', '.dat', '.env',
        '.json', '.xml', '.yaml', '.yml', '.ini', '.cfg', '.conf', '.toml', '.properties',
        '.adoc', '.org', '.lst', '.sbv', '.dfxp', '.ttml', '.dockerfile', '.makefile',
        '.gitattributes', '.gitignore', '.bat', '.ps1',

        # Subtitle files
        '.srt', '.vtt', '.ass', '.ssa', '.sub', '.sbv', '.dfxp', '.ttml', '.stl', '.scc', '.xml', '.cap', '.mcc', '.rt', '.txt', '.lrc', '.usf', '.dks', '.pjs', '.mpl', '.smi', '.psb', '.vtt', '.webvtt', '.tt', '.itt', '.ztt', '.xif', '.subviewer', '.subrip', '.microdvd', '.aqt', '.jss', '.rtf', '.sami', '.sbt', '.vplayer', '.idx', '.sup',

        # Source code files (expanded)
        '.py', '.ipynb', '.pyw', '.pyi',  # Python
        '.js', '.jsx', '.ts', '.tsx',     # JavaScript/TypeScript
        '.java', '.class', '.jar',        # Java
        '.c', '.h', '.cpp', '.cc', '.cxx', '.hpp', '.hh', '.hxx',  # C/C++
        '.cs',                            # C#
        '.go',                            # Go
        '.rb', '.erb',                    # Ruby
        '.php',                           # PHP
        '.html', '.htm', '.xhtml', '.shtml', '.mhtml',  # HTML
        '.css', '.scss', '.less',         # CSS
        '.sh', '.bash', '.zsh', '.ksh',   # Shell scripts
        '.pl', '.pm',                     # Perl
        '.lua',                           # Lua
        '.swift',                         # Swift
        '.kt', '.kts',                    # Kotlin
        '.dart',                          # Dart
        '.scala',                         # Scala
        '.sql',                           # SQL
        '.r', '.R',                       # R
        '.jl',                            # Julia
        '.m', '.mat',                     # MATLAB/Objective-C
        '.vb', '.vbs',                    # Visual Basic
        '.asm', '.s', '.S',               # Assembly
        '.vue',                           # Vue.js
        '.coffee',                        # CoffeeScript
        '.groovy',                        # Groovy
        '.erl', '.hrl',                   # Erlang
        '.ex', '.exs',                    # Elixir
        '.fs', '.fsi', '.fsx', '.fsscript',  # F#
        '.dart',                          # Dart
        '.clj', '.cljs', '.cljc', '.edn',  # Clojure
        '.ml', '.mli', '.ocaml',          # OCaml
        '.hs', '.lhs',                    # Haskell
        '.ps1', '.psm1',                  # PowerShell
        '.sql', '.psql',                  # SQL/PostgreSQL
        '.dockerfile', '.dockerignore',   # Docker
        '.makefile', '.mk',               # Make
        '.cmake', '.gradle', '.pom',      # Build tools
        '.asm', '.s', '.S',               # Assembly
        '.ini', '.cfg', '.conf', '.toml',  # Config
        '.tex', '.bib',                   # LaTeX/BibTeX
        '.yaml', '.yml',                  # YAML
        '.bat', '.cmd',                   # Batch/Windows scripts
        '.properties',                    # Java properties
        '.gitattributes', '.gitignore',   # Git
        '.prj', '.csproj', '.vbproj', '.sln',  # Project files
        '.xaml',                          # XAML
        '.resx',                          # .NET resources
        '.asp', '.aspx', '.ascx',         # ASP.NET
        '.jsp', '.jspx',                  # JSP
        '.rmd',                           # R Markdown
        '.ipynb',                         # Jupyter Notebook
        '.pug', '.jade',                  # Pug/Jade templates
        '.twig',                          # Twig templates
        '.haml',                          # Haml templates
        '.mustache', '.handlebars',       # Mustache/Handlebars
        '.ejs',                           # Embedded JS templates
        '.liquid',                        # Liquid templates
        '.ftl',                           # FreeMarker
        '.hbs',                           # Handlebars
        '.mjml',                          # MJML
        '.tsx', '.jsx',                   # React
        '.vue',                           # Vue.js
        '.scss', '.less',                 # CSS preprocessors
    }

    try:
        all_files = os.listdir(texts_folder)
        text_files = []

        for file in all_files:
            file_lower = file.lower()
            if any(file_lower.endswith(ext) for ext in texts_extensions):
                text_files.append(file)

        # Sort alphabetically for consistent ordering
        return sorted(text_files)
    except Exception as e:
        print(f"Error reading texts folder: {e}")
        return []
