import React, { useState } from 'react';

const CollapsibleList = (props) => {
  const [isOpen, setIsOpen] = useState(false);

  const toggleList = () => {
    setIsOpen(!isOpen);
  };

  return (
    <div>
      <button onClick={toggleList}>
        {isOpen ? '-' : '+'} {props.items[0].category}
      </button>
      {isOpen &&
        <ul>
          {props.items.map((item) => (
            <li key={item.id}>{item.name}</li>
          ))}
        </ul>
      }
    </div>
  );
};

export default CollapsibleList;