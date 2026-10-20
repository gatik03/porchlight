import { useEffect, useRef, useState } from "react";

export interface Card {
  cardId: string;
  accountId: string;
  severity: "calm" | "attention" | "info";
  headline: string;
  sentence: string;
  expectedLine?: string;
  deviceName: string;
  timeLocal: string;
  frameUrl?: string;
  createdAt: string;
  dismissedAt?: string | null;
}

export function usePolling(apiBaseUrl: string, passphrase: string) {
  const [currentCard, setCurrentCard] = useState<Card | null>(null);
  const [isError, setIsError] = useState(false);
  const backoffRef = useRef(2000);
  const sinceRef = useRef<string | null>(null);

  useEffect(() => {
    let isCancelled = false;

    async function poll() {
      if (isCancelled) return;

      const url = sinceRef.current
        ? `${apiBaseUrl}/api/card/current?since=${encodeURIComponent(sinceRef.current)}`
        : `${apiBaseUrl}/api/card/current`;

      try {
        const res = await fetch(url, {
          headers: { "x-porchlight-key": passphrase },
        });

        if (res.status === 200) {
          const card: Card = await res.json();
          setCurrentCard(card);
          sinceRef.current = card.createdAt;
          backoffRef.current = 2000;
        } else if (res.status === 204) {
          // No newer card, keep current state or stay idle
          backoffRef.current = 2000;
        }
        setIsError(false);
      } catch (err) {
        setIsError(true);
        // Exponential backoff up to 30s
        backoffRef.current = Math.min(backoffRef.current * 1.5, 30000);
      } finally {
        if (!isCancelled) {
          setTimeout(poll, backoffRef.current);
        }
      }
    }

    poll();

    return () => {
      isCancelled = true;
    };
  }, [apiBaseUrl, passphrase]);

  const dismiss = async () => {
    setCurrentCard(null);
    try {
      await fetch(`${apiBaseUrl}/api/card/dismiss`, {
        method: "POST",
        headers: { "x-porchlight-key": passphrase },
      });
    } catch (err) {
      // Ignored
    }
  };

  return { currentCard, isError, dismiss };
}
