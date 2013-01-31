Tool to monitor suggested moves and merges at Norwegian Bokmål Wikipedia. 

DB Setup: <code>sqlite3 ffbot.db</code> and 
````
CREATE TABLE moves (
  page TEXT NOT NULL,
  target TEXT NOT NULL,
  target2 TEXT NOT NULL,
  date DATE NOT NULL,
  revid INT NOT NULL,
  parentid INT NOT NULL,
  user TEXT NOT NULL,
  comment TEXT NOT NULL,
  reason TEXT NOT NULL,
  PRIMARY KEY(page)
);
````
