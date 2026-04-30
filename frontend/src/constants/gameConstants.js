// Shared game constants used across Session, FreePlay, and BaselineGameWrapper.

// Maps baseline assessed level (1=Easy, 2=Medium, 3=Hard) to numeric difficulty (1–10).
export const BASELINE_LEVEL_TO_DIFFICULTY = { 1: 2, 2: 5, 3: 8 };

// Maximum number of rounds in a baseline adaptive assessment session.
export const MAX_ROUNDS = 10;

// Starting level for the adaptive baseline algorithm.
export const INITIAL_LEVEL = 1;
