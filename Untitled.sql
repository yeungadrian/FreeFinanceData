CREATE TABLE "kline" (
  "id" SERIAL PRIMARY KEY,
  "symbol" varchar,
  "startTime" timestamp,
  "open" float,
  "high" float,
  "low" float,
  "close" float,
  "volume" float,
  "endTime" timestamp,
  "quoteVolume" float,
  "numTrades" int,
  "buyBaseVolume" float,
  "buyQuoteVolume" float
  
);
