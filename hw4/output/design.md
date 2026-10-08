# Campus Customs: Design

**Concept: vintage Yale varsity.** Think felt letter jackets, pennants, scoreboards, and a library reading room. Every choice below comes back to that idea, so the site feels like one place, not a template.

## Fonts and hierarchy
- **Graduate** (a collegiate block face) for headings, prices, and size letters. It's the "varsity letter" voice and makes the shop recognizable at a glance.
- **Libre Franklin** for body text, buttons, and forms. It's clean and very readable at small sizes, which matters for descriptions and filters.
- **Libre Baskerville italic** for small "academic" touches: the tagline, chat status, sign-offs.
- **Hierarchy:** small gold-ruled kicker ("HOODIES", "PICK YOUR POSITION") → big Graduate heading → Franklin body. Shoppers can scan a page by its kickers and headings and find what they want faster.

## Color
- **Yale blue `#00356b`** and deep navy for the navigation, hero, chat header, and main buttons. **Cream `#f6f0e1`** paper with a faint dot texture as the background, warmer and more "vintage" than plain white. **Old gold** for trim, rules, and calls to action. **Sky blue** for small accents on navy.
- **Readability:** every text pairing passes WCAG AA, checked with the contrast formula: body text 13.7:1, muted text 5.8:1, gold-on-navy 6.3:1, sold-out red 5.7:1. Gold is only used as text on navy, never on cream.
- **One color per meaning:** navy outline = in stock, gold outline = only a few left, red on a striped tile = sold out.

## Motion (tasteful, and turned off for people who prefer reduced motion)
- Pages fade and rise in on every route change. Home sections and product cards cascade in one after another.
- Product cards lift on hover and their photo zooms gently. Category photos tilt slightly. The product page image zooms toward your mouse.
- Shimmering loading placeholders shaped like cards and the product page, so the layout doesn't jump while data loads.
- The chat pops open from its corner, bubbles slide in, and the bulldog on the chat button gives an occasional wiggle.

**Why:** small, consistent motion makes the shop feel alive and responsive, and hover feedback invites clicking into products.

## Product presentation
- **Cards:** a white photo panel, a navy **price tag** pinned to the corner (price is visible instantly), a type kicker, the tidied name, and a row of **size chips** where sold-out sizes are struck through. You can see whether your size exists before clicking.
- **Product page:** a breadcrumb, a large zoomable photo (sticky on laptops), price in the varsity font with a pill like "In stock in 2 of 6 sizes", real color **swatches**, and a **size board**:
  - each size is a tile showing the exact count;
  - "Only 5 left" in gold when stock is low;
  - sold-out sizes are a striped, dashed tile with the size struck through and SOLD OUT in red, plus a small legend.
  - An **"Ask the Bulldog about this"** button opens the chat on the spot.

**Why:** clear price and size information removes the two biggest reasons shoppers hesitate. Low-stock cues add gentle urgency without being pushy.

## Home page (real data only)
1. **Hero:** "Old-school spirit. Brand-new favorites." A drawn pennant, a spinning "CC" badge, and a real product photo with its live price.
2. **Scoreboard:** 102 styles · 11 residential colleges · XS–XXL · from $32. Every number is computed from the database.
3. **Shop by category:** tiles with live counts. Each opens Products with that type already filtered.
4. **Rep your residential college:** one chip per college that has real products. A tap shows that college's items on Products.
5. **Stocked in every size:** the deepest-stocked styles with all six sizes available.
6. **Bulldog pride:** the real "bulldog" search (10 items) with a drawn bulldog.
7. **Ask the Bulldog:** an invitation to chat.

**Why:** many paths into the catalogue (by type, college, pride, or availability) give every visitor an obvious next click.

## The chat
- **A personality:** "The Campus Customs Bulldog", with a hand-drawn bulldog avatar, a green "Checking the real shelves for you" status, and an upbeat "Woof, hi there!" greeting. The agent's prompt was given the same voice, with all the accuracy and safety rules unchanged.
- **Typing indicator:** three hopping dots (navy, gold, navy) with "sniffing out an answer…".
- **Results and suggestions:** suggested questions are pennant-style outlined pills that fill navy on hover. Results show as tidy mini-cards with photo, name, and price, plus "See all on the Products page".
- **On a phone:** the chat becomes a full-width sheet, and the button shrinks to just the bulldog.

**Why:** a friendly, recognizable helper gets more people to ask questions, and shoppers who get answers are more likely to buy.

## Forms, filters, navigation, and phones
- Log in and Create account are "membership card" panels with a striped navy header and the CC monogram. Inputs are large, with a clear focus ring, and errors shake gently.
- Filters sit in a cream panel with varsity-style labels and custom dropdowns.
- The navigation is sticky with a gold underline. On phones it collapses into a menu, the filters go two-across, the size board becomes 3×2, and nothing scrolls sideways (checked at 390 px wide).

All graphics (monogram, pennant, badge, bulldog) are simple shapes drawn in code. No real Yale logos or crests, nothing copied from yalebulldogblue.com, and no changes to the database or product photos.
