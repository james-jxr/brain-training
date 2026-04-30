import React, { useState, useEffect, useCallback } from 'react';
import Button from '../ui/Button';
import Card from '../ui/Card';
import ProgressBar from '../ui/ProgressBar';
import '../styles/CardMemoryGame.css';

const MIN_ROUNDS = 3;

const CardMemoryGame = ({ difficulty, onComplete, totalRounds }) => {
  const shapes = ['◯', '△', '★', '□', '◇'];
  const colors = [
    { hex: 'var(--color-error)', name: 'Red' },
    { hex: 'var(--color-primary)', name: 'Blue' },
    { hex: 'var(--color-success)', name: 'Green' },
    { hex: 'var(--color-purple)', name: 'Purple' },
    { hex: 'var(--color-warning)', name: 'Orange' }
  ];

  const numRounds = Math.max(MIN_ROUNDS, totalRounds || MIN_ROUNDS);

  const getDifficultyString = (numDifficulty) => {
    if (numDifficulty <= 3) return 'easy';
    if (numDifficulty <= 6) return 'medium';
    return 'hard';
  };

  const difficultyString = getDifficultyString(difficulty);

  const difficultyConfig = {
    easy: { cardCount: 4, memorizationTime: 15, shuffleCount: 0 },
    medium: { cardCount: 8, memorizationTime: 15, shuffleCount: 1 },
    hard: { cardCount: 12, memorizationTime: 15, shuffleCount: 2 }
  };

  const config = difficultyConfig[difficultyString] || difficultyConfig.easy;

  const [currentRound, setCurrentRound] = useState(1);
  const [gameState, setGameState] = useState('memorization');
  const [cards, setCards] = useState([]);
  const [cardsRevealed, setCardsRevealed] = useState({});
  const [timeRemaining, setTimeRemaining] = useState(config.memorizationTime);
  const [target, setTarget] = useState(null);
  const [selectedCard, setSelectedCard] = useState(null);
  const [isCorrect, setIsCorrect] = useState(null);
  const [responseStartTime, setResponseStartTime] = useState(null);
  const [responseTime, setResponseTime] = useState(null);
  const [showResult, setShowResult] = useState(false);
  const [score, setScore] = useState(0);
  const [roundResults, setRoundResults] = useState([]);
  const [revealedHint, setRevealedHint] = useState(null);

  const generateCards = useCallback(() => {
    const newCards = [];
    const usedPairs = new Set();

    while (newCards.length < config.cardCount) {
      const shape = shapes[Math.floor(Math.random() * shapes.length)];
      const colorObj = colors[Math.floor(Math.random() * colors.length)];
      const pair = `${shape}-${colorObj.hex}`;

      if (!usedPairs.has(pair)) {
        usedPairs.add(pair);
        newCards.push({
          id: newCards.length,
          shape,
          color: colorObj.hex,
          colorName: colorObj.name,
          pair
        });
      }
    }

    return newCards;
  }, [config.cardCount]);

  const shuffleCards = (cardsToShuffle) => {
    const shuffled = [...cardsToShuffle];
    for (let i = shuffled.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
    }
    return shuffled;
  };

  const initRound = useCallback(() => {
    const newCards = generateCards();
    setCards(newCards);
    const randomCard = newCards[Math.floor(Math.random() * newCards.length)];
    setTarget(randomCard);
    setGameState('memorization');
    setTimeRemaining(config.memorizationTime);
    setSelectedCard(null);
    setIsCorrect(null);
    setResponseStartTime(null);
    setResponseTime(null);
    setShowResult(false);
    setRevealedHint(null);
  }, [generateCards, config.memorizationTime]);

  useEffect(() => {
    initRound();
  }, [currentRound, difficulty]);

  useEffect(() => {
    if (gameState === 'memorization' && timeRemaining > 0) {
      const timer = setTimeout(() => {
        setTimeRemaining(timeRemaining - 1);
      }, 1000);
      return () => clearTimeout(timer);
    }

    if (gameState === 'memorization' && timeRemaining === 0) {
      setGameState('flipping');
      performFlipAndShuffle();
    }
  }, [gameState, timeRemaining]);

  const performFlipAndShuffle = async () => {
    await new Promise(resolve => setTimeout(resolve, 500));

    let currentCards = [...cards];

    for (let i = 0; i < config.shuffleCount; i++) {
      const shuffled = shuffleCards(currentCards);
      setCards(shuffled);
      currentCards = shuffled;
      await new Promise(resolve => setTimeout(resolve, 800));
    }

    setGameState('guessing');
    setResponseStartTime(Date.now());
  };

  const handleCardClick = (cardId) => {
    if (gameState !== 'guessing' || selectedCard !== null || showResult || !responseStartTime || revealedHint !== null) {
      return;
    }

    const clickTime = Date.now();
    const card = cards.find(c => c.id === cardId);
    const correct = card.pair === target.pair;
    const responseTimeMs = clickTime - responseStartTime;

    setSelectedCard(cardId);
    setIsCorrect(correct);

    const speedBonus = calculateSpeedBonus(responseTimeMs, config.memorizationTime);
    const accuracyPoints = correct ? 100 : 0;
    const totalScore = accuracyPoints + speedBonus;

    setScore(totalScore);
    setResponseTime(responseTimeMs);
    setShowResult(true);

    const roundResult = {
      round: currentRound,
      difficulty: difficultyString,
      card_count: config.cardCount,
      correct,
      response_time_ms: Math.round(responseTimeMs),
      score: Math.round(totalScore)
    };

    const updatedResults = [...roundResults, roundResult];
    setRoundResults(updatedResults);

    if (!correct) {
      const matchingCard = cards.find(c => c.pair === target.pair && c.id !== cardId);
      if (matchingCard) {
        setRevealedHint(matchingCard.id);
        setTimeout(() => {
          setRevealedHint(null);
          proceedAfterRound(currentRound, updatedResults, numRounds);
        }, 1500);
        return;
      }
    }

    setTimeout(() => {
      proceedAfterRound(currentRound, updatedResults, numRounds);
    }, 2000);
  };

  const proceedAfterRound = (round, updatedResults, totalRounds) => {
    if (round < totalRounds) {
      setCurrentRound(round + 1);
    } else {
      const totalSessionScore = updatedResults.reduce((sum, r) => sum + r.score, 0);
      const totalCorrect = updatedResults.filter(r => r.correct).length;
      const avgResponseTime = updatedResults.reduce((sum, r) => sum + r.response_time_ms, 0) / updatedResults.length;

      onComplete({
        difficulty: difficultyString,
        card_count: config.cardCount,
        correct: totalCorrect === totalRounds,
        response_time_ms: Math.round(avgResponseTime),
        score: Math.round(totalSessionScore / totalRounds),
        rounds: updatedResults,
        total_rounds: totalRounds,
        rounds_correct: totalCorrect
      });
    }
  };

  const calculateSpeedBonus = (responseTimeMs, memorizationTime) => {
    const windowMs = (15 - memorizationTime) * 1000 + 5000;
    if (responseTimeMs >= windowMs) return 0;
    const bonus = (1 - responseTimeMs / windowMs) * 100;
    return Math.max(0, Math.min(100, bonus));
  };

  const getGridCols = () => {
    if (config.cardCount === 4) return 2;
    if (config.cardCount === 8) return 4;
    return 4;
  };

  const isCardFaceUp = (card) => {
    return selectedCard === card.id || revealedHint === card.id;
  };

  return (
    <div className="card-memory-container">
      <div className="round-indicator">
        Round {currentRound} of {numRounds}
      </div>

      {gameState === 'memorization' && (
        <div className="memorization-phase">
          <div className="instruction">Memorise the card positions!</div>
          <div className={`timer ${timeRemaining <= 3 ? 'warning' : ''}`}>
            {timeRemaining}s
          </div>
          <div className={`card-grid grid-cols-${getGridCols()}`}>
            {cards.map(card => (
              <div key={card.id} className="card-wrapper">
                <div className="card face-up">
                  <div className="card-content" style={{ color: card.color }}>
                    <div className="shape-display">{card.shape}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {(gameState === 'flipping' || gameState === 'guessing') && (
        <div className="guessing-phase">
          {target && (
            <div className="target-display">
              <div className="target-label">Find:</div>
              <div className="target-symbol" style={{ color: target.color }}>
                {target.shape}
              </div>
              <div className="target-description">
                {target.colorName}
                {' '}{getShapeName(target.shape)}
              </div>
            </div>
          )}

          <div className={`card-grid grid-cols-${getGridCols()}`}>
            {cards.map(card => (
              <div
                key={card.id}
                className={`card-wrapper ${
                  selectedCard === card.id ? 'selected' : ''
                } ${
                  revealedHint === card.id ? 'hint-revealed' : ''
                }`}
                onClick={() => handleCardClick(card.id)}
              >
                <div className={`card face-down ${
                  isCardFaceUp(card) ? 'flipped' : ''
                }`}>
                  {isCardFaceUp(card) && (
                    <div className="card-content" style={{ color: card.color }}>
                      <div className="shape-display">{card.shape}</div>
                    </div>
                  )}
                  {!isCardFaceUp(card) && <div className="card-back">?</div>}
                </div>
              </div>
            ))}
          </div>

          {showResult && (
            <div className={`result-message ${isCorrect ? 'correct' : 'incorrect'}`}>
              {isCorrect ? '✓ Correct!' : '✗ Incorrect'}
              <div className="score-display">Score: {Math.round(score)}</div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

const getShapeName = (shape) => {
  const names = {
    '◯': 'Circle',
    '△': 'Triangle',
    '★': 'Star',
    '□': 'Square',
    '◇': 'Diamond'
  };
  return names[shape] || 'Shape';
};

export default CardMemoryGame;
