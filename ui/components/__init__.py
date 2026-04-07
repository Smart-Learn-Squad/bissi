"""UI Components package for BISSI.

Atomic design system with web-styled PyQt6 components.

Structure:
    atoms.py      - Basic building blocks (buttons, inputs, labels)
    molecules.py  - Simple combinations (bubbles, cards, nav items)
    organisms.py  - Complex structures (sidebar, chat area, header)
    complex.py    - Advanced widgets (drop zone, code blocks, markdown)
    theme.py      - Design tokens (colors, typography, spacing)

Example:
    >>> from ui.components import AtomButton, ChatBubble, Sidebar
    >>> btn = AtomButton("Click me", variant="primary")
    >>> bubble = ChatBubble("Hello!", is_user=True)
"""

# Atoms - smallest components
from ui.components.atoms import (
    AtomButton,
    AtomIconButton,
    AtomInput,
    AtomTextArea,
    AtomLabel,
    AtomBadge,
    AtomCheckbox,
    AtomSelect,
    AtomSpinner,
    AtomDivider,
    AtomAvatar,
    AtomTooltip,
    AtomTag,
)

# Molecules - combinations of atoms
from ui.components.molecules import (
    ChatBubble,
    SearchBar,
    FileCard,
    NavItem,
    MessageInput,
    ConversationItem,
)

# Organisms - complex structures
from ui.components.organisms import (
    Sidebar,
    ChatArea,
    Header,
    InputArea,
    WelcomeScreen,
    ToastNotification,
)

# Complex - advanced widgets
from ui.components.complex import (
    FileDropZone,
    CodeBlock,
    MarkdownRenderer,
    FilePreviewCard,
    ThinkingIndicator,
    PersonaSelector,
)

# Theme - design constants
from ui.styles.theme import (
    Colors,
    Typography,
    Spacing,
    Radius,
    Shadows,
    Transitions,
)

__all__ = [
    # Atoms
    "AtomButton",
    "AtomIconButton",
    "AtomInput",
    "AtomTextArea",
    "AtomLabel",
    "AtomBadge",
    "AtomCheckbox",
    "AtomSelect",
    "AtomSpinner",
    "AtomDivider",
    "AtomAvatar",
    "AtomTooltip",
    "AtomTag",
    
    # Molecules
    "ChatBubble",
    "SearchBar",
    "FileCard",
    "NavItem",
    "MessageInput",
    "ConversationItem",
    
    # Organisms
    "Sidebar",
    "ChatArea",
    "Header",
    "InputArea",
    "WelcomeScreen",
    "ToastNotification",
    
    # Complex
    "FileDropZone",
    "CodeBlock",
    "MarkdownRenderer",
    "FilePreviewCard",
    "ThinkingIndicator",
    "PersonaSelector",
    
    # Theme
    "Colors",
    "Typography",
    "Spacing",
    "Radius",
    "Shadows",
    "Transitions",
]
