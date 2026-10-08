# Campus Customs: Usability Improvements

Four improvements, two on the website and two in the agent and backend. Each one is in the running app at http://localhost:5173.

## 1. Filters and sorting on the Products page (website)

**What we added.** A filter bar above the product grid with:
- **Type:** Hoodies, T-Shirts, Crewnecks, Quarter-Zips, Jackets & Fleece, Long Sleeves, Other.
- **Color:** Navy, Gray, White & Cream, Blue, Red, and more.
- **In stock only**, with an optional **size** (e.g. "in stock in M").
- **Sort by price:** low to high, or high to low.

Each choice shows how many items it has. The page shows "Showing X of Y items" and has a **Clear filters** button. If nothing matches, a friendly message explains this and offers to clear the filters.

The database spells the same thing many ways ("pullover hoodie", "hooded sweatshirt", "Hood"; "navy" vs "navy blue"). The backend sorts these into clean groups using the same word-cleaning code as the chatbot's search, so the filters and the chatbot agree.

Filters also work on chat results. When the chat shows search results on the page, you can narrow or sort them too. A new chat search resets the filters so new results are never hidden.

**Why it helps.** Shoppers can get from 102 items to "navy hoodies in my size, cheapest first" in a few clicks. They don't have to scroll or ask the chatbot. Fewer dead ends means fewer people giving up, and showing only sizes that are in stock avoids disappointment at the product page.

## 2. Suggested questions in the chat (website)

**What we added.** When the chat is empty, it shows a few buttons with example questions. Tapping one sends it as a normal message.
- **On most pages:** general questions such as "What hoodies do you have?" or "Is the Basic Hoodie Big Yale in stock?".
- **On a product page:** questions about that product, such as "Do you have this in my size?" or "What colors does this come in?".

**Why it helps.** Many shoppers don't know what a chatbot can do, or what to type. Examples show its strengths (search, stock, comparison) right away, save typing on phones, and get more people using the assistant.

## 3. Sensitive-info guard (agent and backend)

**What we added.** Before a chat message goes to the AI model, the backend checks whether it looks like it contains:
- a **password**, e.g. "my password is …", or
- a **full card number**: 13–19 digits that pass the standard card checksum.

If so, the message is **not sent to the AI model, not saved** in the chat history, and **not written to the logs**. The shopper gets an immediate, friendly warning that the assistant never needs this information. The website also hides the blocked text in the chat window so it isn't sent along later as part of the conversation.

The checks are deliberately narrow, so normal messages like "is it under $70?", "size XL", or "the 2025 Yale vs. Harvard tee" still go through.

**Why it helps.** It protects shoppers who share private details by mistake, and it keeps passwords and card numbers out of a third-party AI service, our database, and our logs. This lowers the shop's privacy and security risk.

## 4. Product comparison tool (agent and backend)

**What we added.** A new chatbot tool, `compare_products`, that compares two or three products side by side using only the database: price, colors, and stock by size. It also works out which product is cheapest, the price difference, and which sizes are in stock in all of them.

The agent uses it for questions like "Which is cheaper, the Morse quarter-zip or the Berkeley quarter-zip?" or "compare these two hoodies". If a name matches several products or none, the agent asks or says so honestly, just like the single-product lookup. Answers stay short: the key difference, not every number.

**Why it helps.** Choosing between similar items (e.g. two college quarter-zips) is a common moment of hesitation before buying. A quick, accurate comparison helps shoppers decide with confidence, and since every number comes from the database, it can never quote a wrong price.
