import type { Transition, Variants } from "framer-motion";

export const EASE_OUT_EXPO = [0.16, 1, 0.3, 1] as const;

export const transitionExpo: Transition = {
  duration: 0.75,
  ease: EASE_OUT_EXPO,
};

export const springInteractive: Transition = {
  type: "spring",
  stiffness: 260,
  damping: 30,
};

export const springSnappy: Transition = {
  type: "spring",
  stiffness: 350,
  damping: 25,
};

export const containerStagger = (stagger = 0.05, delay = 0): Variants => ({
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: stagger,
      delayChildren: delay,
    },
  },
});

export const itemSlideUp: Variants = {
  hidden: { opacity: 0, y: 24 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.7, ease: EASE_OUT_EXPO },
  },
};

export const itemFade: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { duration: 0.6, ease: EASE_OUT_EXPO },
  },
};

export const itemScale: Variants = {
  hidden: { opacity: 0, scale: 0.95 },
  visible: {
    opacity: 1,
    scale: 1,
    transition: { duration: 0.5, ease: EASE_OUT_EXPO },
  },
};

export const pageTransition: Variants = {
  hidden: { opacity: 0, y: 12 },
  enter: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.6, ease: EASE_OUT_EXPO },
  },
  exit: {
    opacity: 0,
    y: -8,
    transition: { duration: 0.3, ease: EASE_OUT_EXPO },
  },
};
