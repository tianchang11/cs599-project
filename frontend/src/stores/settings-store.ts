import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { LLMProvider } from "@/types";

interface SettingsState {
  provider: LLMProvider;
  apiKey: string;
  model: string;
  deviceId: string;
  setProvider: (p: LLMProvider) => void;
  setApiKey: (k: string) => void;
  setModel: (m: string) => void;
}

function generateDeviceId() {
  return "device_" + Math.random().toString(36).substring(2) + Date.now().toString(36);
}

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set) => ({
      provider: "openai",
      apiKey: "",
      model: "gpt-4o",
      deviceId: generateDeviceId(),
      setProvider: (p) => set({ provider: p }),
      setApiKey: (k) => set({ apiKey: k }),
      setModel: (m) => set({ model: m }),
    }),
    {
      name: "deep-research-settings",
    }
  )
);
