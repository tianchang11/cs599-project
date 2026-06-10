"use client";

import { useEffect, useState } from "react";

interface LoadingProps {
  message?: string;
  fullScreen?: boolean;
}

export function Loading({ message = "加载中...", fullScreen = false }: LoadingProps) {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setVisible(true), 200);
    return () => clearTimeout(timer);
  }, []);

  if (!visible) return null;

  const spinner = (
    <div className="h-8 w-8 rounded-full border-2 border-primary border-t-transparent animate-spin" />
  );

  if (fullScreen) {
    return (
      <div className="fixed inset-0 flex items-center justify-center bg-background/80 backdrop-blur-sm z-50">
        <div className="text-center">
          {spinner}
          {message && <p className="mt-3 text-sm text-muted-foreground">{message}</p>}
        </div>
      </div>
    );
  }

  return (
    <div className="flex items-center justify-center py-8 gap-3">
      {spinner}
      {message && <p className="text-sm text-muted-foreground">{message}</p>}
    </div>
  );
}
