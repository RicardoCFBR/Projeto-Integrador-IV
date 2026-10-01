/** Deterministic PRNG (mulberry32) so mock data stays stable across reloads. */
export function createSeededRandom(seed: number): () => number {
  let state = seed >>> 0;
  return () => {
    state = (state + 0x6d2b79f5) >>> 0;
    let t = state;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export function round1(value: number): number {
  return Math.round(value * 10) / 10;
}

export function randomBetween(rand: () => number, min: number, max: number): number {
  return min + rand() * (max - min);
}

/** Sorteia enviesado para o topo do intervalo (maioria dos valores perto de `max`). */
export function skewedHighBetween(rand: () => number, min: number, max: number, power = 3): number {
  return max - (max - min) * rand() ** power;
}
