import { useEffect, useState } from "react";
import { doc, onSnapshot } from "firebase/firestore";
import { db } from "../firebase";

function parseFirestoreTimestamp(ts) {
  if (!ts) return null;

  if (typeof ts.toDate === "function") {
    return ts.toDate();
  }

  if (typeof ts.seconds === "number") {
    return new Date(ts.seconds * 1000);
  }

  return null;
}

function formatDateLabel(dateObj) {
  if (!dateObj) return "";
  return dateObj.toISOString().slice(0, 10);
}

export function useInvestmentEvolution() {
  const [points, setPoints] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const ref = doc(db, "investmentEvolutions", "user1");

    const unsubscribe = onSnapshot(
      ref,
      (snapshot) => {
        const docData = snapshot.data();
        const arr = Array.isArray(docData?.array) ? docData.array : [];
        const normalized = arr.map((item) => {
          const d = parseFirestoreTimestamp(item.date);
          return {
            date: d,
            dateLabel: formatDateLabel(d),
            portfolioValue: item.portfolioValue ?? 0,
            portfolioIndex: item.portfolioIndex ?? 0,
            dailyReturn: item.dailyReturn ?? 0,
            contributions: item.contributions ?? 0,
          };
        });

        setPoints(normalized);
        setLoading(false);
      },
      (error) => {
        console.error("Error listening investmentEvolutions/user1:", error);
        setLoading(false);
      }
    );

    return () => unsubscribe();
  }, []);

  return { points, loading };
}
