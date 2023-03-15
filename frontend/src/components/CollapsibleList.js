import React, { useState } from 'react';

const CollapsibleList = (props) => {
  const [isOpen, setIsOpen] = useState(false);

  const toggleList = () => {
    setIsOpen(!isOpen);
  };

  return (
    <>
      <div>
        <button onClick={toggleList}>
          {isOpen ? '-' : '+'} {props.type}
        </button>
        {isOpen &&
          <ul>
            {props.list.map((item, index) => (
              <li key={index}>{item.operation} {item.sym} {item.amount} {item.date}</li>
            ))}
          </ul>
        }
      </div>
    </>
  );
};

export default CollapsibleList;