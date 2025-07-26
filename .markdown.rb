# MD026: Trailing punctuation in header - Disallows headers ending with specified punctuation characters
rule 'MD026', :punctuation => '.,;:!'

# MD013: Line length - Enforces a maximum line length, but ignores code blocks
rule 'MD013', :ignore_code_blocks => true

# MD033: Inline HTML - This rule is excluded, allowing inline HTML in Markdown files
exclude_rule 'MD033'
