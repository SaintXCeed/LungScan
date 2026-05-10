'use client';
import React from 'react';
import { Button } from '../ui/button';
import { InfiniteSlider } from '../ui/infinite-slider';
import { ChevronRight } from 'lucide-react';
import kemenkesLogo from '../../assets/logo/kemenkesri.png';
import bpjsLogo from '../../assets/logo/bpjs-kesehatan.png';
import halodocLogo from '../../assets/logo/halodoc.png';
import siloamLogo from '../../assets/logo/SiloamHospital.png';
import alodokterLogo from '../../assets/logo/Alodokter.png';

export function HeroSection() {
    const scrollToUpload = (e: React.MouseEvent) => {
        e.preventDefault();
        const element = document.getElementById('upload-section');
        if (element) {
            element.scrollIntoView({ behavior: 'smooth' });
        }
    };

    return (
        <main className="overflow-x-hidden relative min-h-screen flex flex-col justify-between">
            {/* Full-screen Background Video */}
            <div className="absolute inset-0 z-0 overflow-hidden">
                <video
                    autoPlay
                    loop
                    muted
                    playsInline
                    className="w-full h-full object-cover opacity-80 scale-105"
                    src="https://ik.imagekit.io/lrigu76hy/tailark/dna-video.mp4?updatedAt=1745736251477"></video>
                <div className="absolute inset-0 bg-navy-900/60"></div>
                <div className="absolute inset-0 bg-gradient-to-b from-navy-900/50 via-transparent to-navy-900/90"></div>
            </div>

            {/* Ambient Background Glows */}
            <div className="absolute top-0 left-[-10%] w-[50%] h-[50%] bg-emerald-500/20 blur-[120px] rounded-full pointer-events-none z-0" />
            <div className="absolute bottom-[20%] right-[-10%] w-[40%] h-[40%] bg-cyan-500/10 blur-[100px] rounded-full pointer-events-none z-0" />

            <section className="relative z-10 flex-1 flex flex-col justify-center">
                <div className="mx-auto flex w-full max-w-7xl flex-col px-6 lg:px-12 pt-32 pb-24">
                    <div className="max-w-2xl text-center lg:text-left">
                        


                        <h1 className="mt-4 text-balance text-5xl md:text-6xl lg:text-[5rem] font-extrabold tracking-tight leading-[1.1] text-white drop-shadow-xl">
                            Deteksi Dini Kanker Paru <br />
                            <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-cyan-400 drop-shadow-sm">
                                Cepat & Akurat.
                            </span>
                        </h1>
                        <p className="mt-8 text-balance text-lg md:text-xl text-gray-300 font-medium leading-relaxed drop-shadow-md">
                            Terkadang gejala klinis muncul terlalu lambat. Melalui pendekatan kecerdasan buatan berbasis <b className="text-white">Deep Learning</b>, platform kami membantu mendeteksi anomali pada CT-Scan sejak tahap awal, memberi Anda lebih banyak waktu untuk langkah preventif krusial.
                        </p>

                        <div className="mt-12 flex flex-col items-center gap-4 sm:flex-row lg:justify-start">
                            <Button
                                size="lg"
                                onClick={scrollToUpload}
                                className="h-14 rounded-full pl-6 pr-4 text-base font-bold w-full sm:w-auto bg-emerald-500 text-white shadow-[0_0_20px_rgba(16,185,129,0.4)] hover:shadow-[0_0_30px_rgba(16,185,129,0.6)] transition-all border-none">
                                <span className="text-nowrap drop-shadow-md">Mulai Deteksi Sekarang</span>
                                <ChevronRight className="ml-1 w-5 h-5" />
                            </Button>
                            <Button
                                size="lg"
                                variant="outline"
                                onClick={() => {
                                    const el = document.getElementById('heatmap-example');
                                    if (el) el.scrollIntoView({ behavior: 'smooth' });
                                }}
                                className="h-14 rounded-full px-6 text-base font-semibold w-full sm:w-auto bg-navy-900/30 backdrop-blur-md hover:bg-white hover:text-navy-900 border-white/20 text-white shadow-lg transition-colors">
                                <span className="text-nowrap">Pelajari Cara Kerja AI</span>
                            </Button>
                        </div>
                    </div>
                </div>
            </section>

            <section className="bg-transparent pb-12 pt-12 relative z-10">
                <div className="group relative m-auto max-w-7xl px-6">
                    <div className="flex flex-col items-center md:flex-row border-t border-white/10 pt-8">
                        <div className="md:max-w-[200px] md:border-r border-white/10 md:pr-8 mb-6 md:mb-0">
                            <p className="text-center md:text-end text-sm text-gray-500 font-medium">Dipercaya oleh institusi medis & riset terdepan</p>
                        </div>
                        <div className="relative py-6 md:w-[calc(100%-200px)] overflow-hidden">
                            <InfiniteSlider
                                duration={40}
                                gap={80}>
                                <div className="flex items-center gap-3 text-gray-300 hover:text-white transition-colors grayscale hover:grayscale-0">
                                    <img src={kemenkesLogo} alt="Kemenkes RI" className="h-10 w-auto object-contain rounded-full bg-white/10" />
                                    <span className="font-bold text-lg tracking-tight hidden sm:block">Kemenkes RI</span>
                                </div>
                                <div className="flex items-center gap-3 text-gray-300 hover:text-white transition-colors grayscale hover:grayscale-0">
                                    <img src={bpjsLogo} alt="BPJS Kesehatan" className="h-10 w-auto object-contain rounded-full bg-white/10" />
                                    <span className="font-bold text-lg tracking-tight hidden sm:block">BPJS Kesehatan</span>
                                </div>
                                <div className="flex items-center gap-3 text-gray-300 hover:text-white transition-colors grayscale hover:grayscale-0">
                                    <img src={halodocLogo} alt="Halodoc" className="h-10 w-auto object-contain rounded-full bg-white/10" />
                                    <span className="font-bold text-lg tracking-tight hidden sm:block">Halodoc</span>
                                </div>
                                <div className="flex items-center gap-3 text-gray-300 hover:text-white transition-colors grayscale hover:grayscale-0">
                                    <img src={siloamLogo} alt="Siloam Hospitals" className="h-10 w-auto object-contain rounded-full bg-white/10" />
                                    <span className="font-bold text-lg tracking-tight hidden sm:block">Siloam Hospitals</span>
                                </div>
                                <div className="flex items-center gap-3 text-gray-300 hover:text-white transition-colors grayscale hover:grayscale-0">
                                    <img src={alodokterLogo} alt="Alodokter" className="h-10 w-auto object-contain rounded-full bg-white/10" />
                                    <span className="font-bold text-lg tracking-tight hidden sm:block">Alodokter</span>
                                </div>
                            </InfiniteSlider>

                            <div className="bg-gradient-to-r from-navy-900 absolute inset-y-0 left-0 w-24 z-10 pointer-events-none"></div>
                            <div className="bg-gradient-to-l from-navy-900 absolute inset-y-0 right-0 w-24 z-10 pointer-events-none"></div>
                        </div>
                    </div>
                </div>
            </section>
        </main>
    )
}
