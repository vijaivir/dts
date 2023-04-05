import React, { useState, useEffect } from 'react';

const Countdown = () => {
  const [timeLeft, setTimeLeft] = useState(60);

  useEffect(() => {
    // If there is no time left, return to prevent an additional interval
    if (timeLeft === 0) {
      return;
    }

    // Set up the countdown interval
    const countdown = setInterval(() => {
      setTimeLeft(timeLeft - 1);
    }, 1000);

    // Clean up the interval when the effect is finished
    return () => clearInterval(countdown);
  }, [timeLeft]);

  return (
    <div>
      <p>Time left: {timeLeft} seconds</p>
    </div>
  );
};

export default Countdown;