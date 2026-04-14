# DFA Minimizer Visualizer

###  Live Demo:

https://dfa-minimizer-six.vercel.app/



##  Overview

A browser-based tool to **visualize and minimize Deterministic Finite Automata (DFA)**.

This project allows users to input a DFA, perform minimization using standard algorithms, and visually understand how equivalent states are merged to produce an optimized DFA.



##  Features

* Input custom DFA (states, alphabet, transitions)
* Automatic DFA minimization
* Step-by-step state partitioning
* Visualization of minimized DFA
* Handles unreachable and equivalent states
* Clean and interactive UI



##  Project Structure

```
.
├── index.html        # UI layout and entry point
├── api/              # Backend logic (if used)
├── main.py           # DFA minimization logic
├── main2.py          # Supporting logic
├── requirements.txt  # Dependencies
├── vercel.json       # Deployment configuration
```



##  Usage

1. Open the live demo link
2. Enter:

   * States
   * Alphabet
   * Transition table
   * Start state
   * Final states
3. Click on **Minimize DFA**
4. View:

   * Intermediate steps
   * Final minimized DFA



##  How It Works

* Removes unreachable states
* Groups equivalent states
* Applies partitioning algorithm
* Generates minimized DFA



##  Notes

* Input format must be correct for accurate results
* DFA should be deterministic (no multiple transitions for same input)
* Useful for understanding automata theory concepts
* Designed for educational purposes



##  Run Locally

1. Clone the repository
2. Install dependencies:

   ```
   pip install -r requirements.txt
   ```
3. Run the backend:

   ```
   python main.py
   ```
4. Open `index.html` in browser



##  Technologies Used

* HTML, CSS, JavaScript
* Python (for backend logic)
* Vercel (for deployment)


