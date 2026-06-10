---
name: frontend-ui-engineering
description: Builds production-quality UIs with design system adherence, accessibility, and responsive design.
---

# Frontend UI Engineering

## Component Architecture
- Colocate everything related to a component
- Prefer composition over configuration
- Separate data fetching from presentation
- Keep components focused (one thing per component)

## State Management
Local state (useState) → Lifted state → Context → URL state → Server state → Global store

## Avoid the AI Aesthetic
| AI Default | Production Quality |
|-----------|-------------------|
| Purple/indigo everything | Project's actual color palette |
| Excessive gradients | Flat or subtle gradients from design system |
| Rounded everything (rounded-2xl) | Consistent border-radius from design system |
| Stock card grids | Purpose-driven layouts |
| Oversized padding | Consistent spacing scale |

## Accessibility (WCAG 2.1 AA)
- Every interactive element keyboard accessible
- ARIA labels on elements without visible text
- Focus management when content changes
- Meaningful empty states (not blank screens)

## Responsive Design
Mobile first: `grid-cols-1 sm:grid-cols-2 lg:grid-cols-3`

## Verification
- [ ] No console errors
- [ ] Keyboard accessible (Tab through page)
- [ ] Responsive at 320px, 768px, 1024px, 1440px
- [ ] Loading/error/empty states handled
- [ ] Design system tokens used (not raw hex/px values)
