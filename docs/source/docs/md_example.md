
# Markdown Example Title

This file is written using Markdown.

## Section Header

Let's try some code:

```python

    def __init__(self, width=32):
        super().__init__()
        self.value = Signal(width)
        self.set = Signal()

    def elab(self, m):
        m.d.sync += self.set.eq(0)
        with m.If(self.start):
            m.d.sync += self.value.eq(self.in0),
            m.d.sync += self.set.eq(1),
            m.d.comb += self.output.eq(self.value)
            m.d.comb += self.done.eq(1)


```

### Subsection Header

We have a list.

* item1
* item2
* item3

Make an edit to check PR webhook.
Another edit.

