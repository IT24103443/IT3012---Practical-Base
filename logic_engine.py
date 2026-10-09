class KnowledgeBase:
    """Stores facts (current percepts) and rules (Horn clauses)."""

    def __init__(self):
        self.facts = set()   # unique string facts, e.g. "TargetVisible"
        self.rules = []      # list of tuples: ([premises], "conclusion")

    def tell_fact(self, fact_string):
        """Add a single fact to the KB."""
        self.facts.add(fact_string)

    def tell_rule(self, premise_list, conclusion_string):
        """Add a Horn clause: premise1 AND premise2 AND ... => conclusion."""
        self.rules.append((list(premise_list), conclusion_string))

    def clear_facts(self):
        """Forget all facts (rules are kept)."""
        self.facts.clear()

    def forward_chain(self):
        """Data-driven forward chaining.

        Keep sweeping over the rules, firing any rule whose premises are all
        known facts (Modus Ponens), until a full pass adds no new fact.
        """
        new_facts_added = True

        while new_facts_added:
            new_facts_added = False

            for premises, conclusion in self.rules:
                if conclusion not in self.facts:
                    # Modus Ponens check: all premises true => conclusion true
                    if all(p in self.facts for p in premises):
                        self.facts.add(conclusion)
                        new_facts_added = True

        return self.facts