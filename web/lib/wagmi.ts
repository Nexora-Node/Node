"use client";
import { getDefaultConfig } from "@rainbow-me/rainbowkit";
import { mainnet, base, optimism, bsc } from "wagmi/chains";

export const wagmiConfig = getDefaultConfig({
  appName: "Nexora",
  projectId: process.env.NEXT_PUBLIC_WALLETCONNECT_PROJECT_ID || "nexora-node",
  chains: [mainnet, base, optimism, bsc],
  ssr: true,
});
