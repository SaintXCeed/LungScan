import * as React from "react";
import { ArrowRight } from "lucide-react";
import { cn } from "../../lib/utils";

export interface ProjectCardProps extends React.HTMLAttributes<HTMLDivElement> {
  imgSrc: string;
  title: string;
  description: string;
  link: string;
  linkText?: string;
}

const ProjectCard = React.forwardRef<HTMLDivElement, ProjectCardProps>(
  ({ className, imgSrc, title, description, link, linkText = "Pelajari Lebih Lanjut", ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          "group relative flex cursor-pointer flex-col overflow-hidden rounded-2xl border border-white/10 bg-navy-800 text-white shadow-lg transition-all duration-500 ease-in-out hover:-translate-y-2 hover:shadow-emerald-500/20 hover:shadow-2xl",
          className
        )}
        {...props}
      >
        {/* Card Image Section */}
        <div className="aspect-video overflow-hidden border-b border-white/10">
          <img
            src={imgSrc}
            alt={title}
            className="h-full w-full object-cover transition-transform duration-700 ease-in-out group-hover:scale-110"
            loading="lazy"
          />
        </div>

        {/* Card Content Section */}
        <div className="flex flex-1 flex-col p-6">
          <h3 className="text-xl font-bold transition-colors duration-300 group-hover:text-emerald-400">
            {title}
          </h3>
          <p className="mt-3 flex-1 text-gray-400 font-light leading-relaxed">{description}</p>
          
          {/* Card Link/CTA */}
          <a
            href={link}
            className="group/button mt-6 inline-flex items-center gap-2 text-sm font-semibold text-emerald-400 transition-all duration-300 hover:text-emerald-300"
            onClick={(e) => e.stopPropagation()} 
          >
            {linkText}
            <ArrowRight className="h-4 w-4 transition-transform duration-300 group-hover/button:translate-x-1" />
          </a>
        </div>
      </div>
    );
  }
);
ProjectCard.displayName = "ProjectCard";

export { ProjectCard };
