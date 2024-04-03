from kaleido.scopes.mermaid import MermaidScope

scope = MermaidScope()

graphDefinition = """
    graph LR
    A --- B
    B-->C[fa:fa-ban forbidden]
    B-->D(fa:fa-spinner);
    """

data = scope.transform(graphDefinition, format="svg")
print(data)