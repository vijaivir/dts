import React, { useState, useEffect } from 'react';

const CollapsibleList = (props) => {
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    props.refreshUserInfo()
  }, [isOpen]);

  const toggleList = () => {
    setIsOpen(!isOpen);
  };

  console.log(props.list)

  return (
    <>
      <div>
        <button onClick={toggleList}>
          {isOpen ? '-' : '+'} {props.type}
        </button>
        {isOpen &&
          <ul>
            {props.list.map((item, index) => (
              <li key={index}>{item.command} {item.sym} {item.amount} {item.timestamp}</li>
            ))}
          </ul>
        }
      </div>
    </>
  );
};

export default CollapsibleList;