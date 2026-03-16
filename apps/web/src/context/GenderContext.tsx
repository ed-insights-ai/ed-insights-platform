"use client";

import { createContext, useContext, useState, ReactNode } from "react";

type Gender = "men" | "women";

interface GenderContextValue {
  gender: Gender;
  setGender: (g: Gender) => void;
}

const GenderContext = createContext<GenderContextValue>({
  gender: "men",
  setGender: () => {},
});

export function GenderProvider({ children }: { children: ReactNode }) {
  const [gender, setGender] = useState<Gender>("men");
  return (
    <GenderContext.Provider value={{ gender, setGender }}>
      {children}
    </GenderContext.Provider>
  );
}

export function useGender() {
  return useContext(GenderContext);
}
