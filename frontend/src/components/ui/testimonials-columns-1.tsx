"use client";
import React from "react";
import { motion } from "framer-motion";

export const TestimonialsColumn = (props: {
  className?: string;
  testimonials: { text: string; image: string; name: string; role: string }[];
  duration?: number;
}) => {
  return (
    <div className={props.className}>
      <motion.div
        animate={{
          translateY: "-50%",
        }}
        transition={{
          duration: props.duration || 10,
          repeat: Infinity,
          ease: "linear",
          repeatType: "loop",
        }}
        className="flex flex-col gap-6 pb-6 bg-transparent"
      >
        {[...new Array(2).fill(0)].map((_, index) => (
          <React.Fragment key={index}>
            {props.testimonials.map(({ text, image, name, role }, i) => (
              <div className="p-8 rounded-3xl border border-white/10 shadow-lg shadow-emerald-500/5 max-w-xs w-full bg-surface/50 backdrop-blur-sm" key={i}>
                <div className="text-sm text-gray-300 leading-relaxed">"{text}"</div>
                <div className="flex items-center gap-3 mt-6">
                  <img
                    width={40}
                    height={40}
                    src={image}
                    alt={name}
                    className="h-10 w-10 rounded-full border border-white/20 object-cover"
                  />
                  <div className="flex flex-col">
                    <div className="font-semibold tracking-tight leading-5 text-white">{name}</div>
                    <div className="text-xs leading-5 text-emerald-400 tracking-tight">{role}</div>
                  </div>
                </div>
              </div>
            ))}
          </React.Fragment>
        ))}
      </motion.div>
    </div>
  );
};
