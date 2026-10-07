"use client";

import { useRef } from "react";
import type { ComponentProps } from "react";
import gsap from "gsap";
import Flip from "gsap/Flip";

gsap.registerPlugin(Flip);

type FlipRevealItemProps = {
  flipKey: string;
} & ComponentProps<"div">;

export const FlipRevealItem = ({ flipKey, ...props }: FlipRevealItemProps) => {
  return <div data-flip={flipKey} {...props} />;
};

type FlipRevealProps = {
  keys: string[];
  showClass?: string;
  hideClass?: string;
} & ComponentProps<"div">;

export const FlipReveal = ({
  keys,
  hideClass = "",
  showClass = "",
  ...props
}: FlipRevealProps) => {
  const wrapperRef = useRef<HTMLDivElement | null>(null);

  const isShow = (key: string | null) =>
    !!key && (keys.includes("all") || keys.includes(key));

  // Use useEffect instead of useGSAP to avoid @gsap/react peer-dep issues
  const prevKeysRef = useRef<string[]>([]);

  const runFlip = () => {
    if (!wrapperRef.current) return;
    const items = gsap.utils.toArray<HTMLDivElement>("[data-flip]");
    const state = Flip.getState(items);

    items.forEach((item) => {
      const key = item.getAttribute("data-flip");
      if (isShow(key)) {
        item.classList.add(...(showClass ? [showClass] : []));
        item.classList.remove(...(hideClass ? [hideClass] : []));
      } else {
        item.classList.remove(...(showClass ? [showClass] : []));
        item.classList.add(...(hideClass ? [hideClass] : []));
      }
    });

    Flip.from(state, {
      duration: 0.5,
      scale: true,
      ease: "power1.inOut",
      stagger: 0.04,
      absolute: true,
      onEnter: (elements) =>
        gsap.fromTo(
          elements,
          { opacity: 0, scale: 0.7 },
          { opacity: 1, scale: 1, duration: 0.5 }
        ),
      onLeave: (elements) =>
        gsap.to(elements, { opacity: 0, scale: 0.7, duration: 0.4 }),
    });
  };

  // Run on keys change
  const keysStr = JSON.stringify(keys);
  if (keysStr !== JSON.stringify(prevKeysRef.current)) {
    prevKeysRef.current = keys;
    // Defer to after render
    setTimeout(runFlip, 0);
  }

  return <div {...props} ref={wrapperRef} />;
};
