export const gymInfo = {
  name: 'FitZone',
  phone: '+919000000000',
  phoneDisplay: '+91 90000 00000',
  whatsapp: '919000000000',
  email: 'hello@fitzone.example',
  address: 'Indiranagar, Bengaluru, Karnataka 560038',
  shortAddress: 'Indiranagar, Bengaluru',
  hours: [
    { days: 'Monday – Saturday', time: '6:00 AM – 10:00 PM' },
    { days: 'Sunday', time: '7:00 AM – 1:00 PM' },
  ],
  mapsUrl: 'https://maps.google.com/?q=FitZone+Indiranagar+Bengaluru',
}

export const socialLinks = [
  { name: 'Instagram', href: 'https://instagram.com/' },
  { name: 'Facebook', href: 'https://facebook.com/' },
  { name: 'YouTube', href: 'https://youtube.com/' },
]

export const siteImages = {
  hero: '/images/hero.jpg',
  about: '/images/about.jpg',
  strength: '/images/strength.jpg',
  cardio: '/images/weight-loss.jpg',
  training: '/images/functional-training.jpg',
  personalTraining: '/images/personal-training.jpg',
  bodybuilder: '/images/bodybuilder.webp',
}

export const membershipPlans = [
  {
    name: 'Basic',
    price: '₹1,200',
    period: '/ month',
    description: 'A strong start to your training routine.',
    features: ['Full gym access', 'All equipment', 'Locker facility', 'Basic guidance'],
  },
  {
    name: 'Pro',
    price: '₹1,500',
    period: '/ month',
    description: 'Extra coaching for consistent progress.',
    popular: true,
    features: [
      'Full gym access',
      'All equipment',
      'Locker facility',
      'Personal guidance',
      'Diet support',
    ],
  },
  {
    name: 'Elite',
    price: '₹2,500',
    period: '/ month',
    description: 'Priority support for your biggest goals.',
    features: [
      'Full gym access',
      'All equipment',
      'Locker facility',
      'Personal guidance',
      'Diet support',
      'Priority support',
    ],
  },
]

export const membershipPasses = [
  { duration: '3 Months', price: '₹3,000', detail: 'A focused start to your routine.' },
  { duration: '6 Months', price: '₹5,500', detail: 'More time to build momentum.' },
]

export const trainerProfiles = [
  {
    name: 'Arjun',
    role: 'Head Trainer',
    experience: '5+ Years Experience',
    specialization: 'Strength Training / Weight Loss',
    description: 'Practical, progressive coaching built around your starting point.',
    image:
      'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?auto=format&fit=crop&w=850&q=80',
  },
  {
    name: 'Rohit',
    role: 'Fitness Coach',
    experience: '4+ Years Experience',
    specialization: 'Bodybuilding / Personal Training',
    description: 'Form-first strength sessions with a clear plan for every rep.',
    image:
      'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&w=850&q=80',
  },
  {
    name: 'Vikram',
    role: 'Cardio & Functional Coach',
    experience: '3+ Years Experience',
    specialization: 'Cardio / Functional Training',
    description: 'Energetic sessions to help you move well and build lasting fitness.',
    image:
      'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=850&q=80',
  },
]

export const facilityItems = [
  {
    title: 'Strength Training',
    description: 'Build strength with progressive training and dependable equipment.',
    icon: 'strength',
    image: siteImages.strength,
  },
  {
    title: 'Cardio Zone',
    description: 'Dedicated space for conditioning, endurance, and steady-state work.',
    icon: 'cardio',
    image: siteImages.cardio,
  },
  {
    title: 'Free Weights',
    description: 'Room to move through focused dumbbell, barbell, and rack work.',
    icon: 'weights',
    image: siteImages.bodybuilder,
  },
  {
    title: 'Functional Training',
    description: 'Train balance, coordination, and athletic movement patterns.',
    icon: 'functional',
    image: siteImages.training,
  },
  {
    title: 'Personal Training',
    description: 'One-to-one guidance to help you train safely and with purpose.',
    icon: 'personal',
    image: siteImages.personalTraining,
  },
  {
    title: 'Changing Room',
    description: 'A clean, comfortable place to get ready before and after training.',
    icon: 'changing',
    image: siteImages.about,
  },
]

export const homeFacilities = [
  { ...facilityItems[0], image: siteImages.strength },
  { ...facilityItems[1], image: siteImages.cardio },
  { ...facilityItems[2], image: siteImages.bodybuilder },
  { ...facilityItems[3], image: siteImages.training },
]

export const trainingPrograms = [
  {
    title: 'Muscle Building',
    text: 'A structured plan for building muscle, improving form, and training with intent.',
    image: siteImages.training,
    icon: 'strength',
    number: '01',
  },
  {
    title: 'Weight Loss',
    text: 'Sustainable coaching that balances strength, conditioning, and consistency.',
    image: siteImages.cardio,
    icon: 'cardio',
    number: '02',
  },
  {
    title: 'Strength Training',
    text: 'Build confidence under the bar with progressive, expert-led programming.',
    image: siteImages.strength,
    icon: 'weights',
    number: '03',
  },
  {
    title: 'Functional Fitness',
    text: 'Move better and feel stronger with varied, full-body training sessions.',
    image: siteImages.training,
    icon: 'functional',
    number: '04',
  },
]

export const homeMembershipPlans = membershipPlans.map((plan) => ({
  ...plan,
  note: plan.name === 'Basic'
    ? 'For your everyday training'
    : plan.name === 'Pro'
      ? 'The complete training experience'
      : 'More coaching. More support.',
  features: plan.features.slice(0, 3),
}))

export const homeTrainers = trainerProfiles.map((trainer) => ({
  ...trainer,
  specialty: trainer.specialization.replace(' / ', ' & '),
}))

export const testimonials = [
  {
    name: 'Nisha S.',
    result: 'Stronger in 12 weeks',
    quote: 'I found a routine I can actually stick to. The coaching made all the difference.',
    image: siteImages.about,
    stat: '+32% strength',
  },
  {
    name: 'Karan P.',
    result: 'A new level of confidence',
    quote: 'Every session feels purposeful. I am lifting better and feeling better.',
    image: siteImages.bodybuilder,
    stat: '4 days / week',
  },
  {
    name: 'Aditi R.',
    result: 'Fitness that fits real life',
    quote: 'The team helped me build consistency without making training feel intimidating.',
    image: siteImages.personalTraining,
    stat: '12-week program',
  },
]

export const galleryItems = [
  { title: 'The Training Floor', category: 'GYM', image: siteImages.hero },
  { title: 'Strength Station', category: 'EQUIPMENT', image: siteImages.strength },
  { title: 'Coach-led Session', category: 'TRAINING', image: siteImages.training },
  { title: 'Personal Coaching', category: 'TRAINERS', image: siteImages.personalTraining },
  { title: 'A Stronger Routine', category: 'MEMBERS', image: siteImages.about },
  { title: 'Built Through Consistency', category: 'TRANSFORMATIONS', image: siteImages.bodybuilder },
  { title: 'Cardio & Conditioning', category: 'TRAINING', image: siteImages.cardio },
  { title: 'Free Weights', category: 'EQUIPMENT', image: siteImages.bodybuilder },
  { title: `Inside ${gymInfo.name}`, category: 'GYM', image: siteImages.about },
]
