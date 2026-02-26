import Link from 'next/link';

export default function Home() {
  return (
    <main className="min-h-screen bg-gradient-to-br from-pink-50 via-purple-50 to-blue-50">
      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <h1 className="text-2xl font-bold text-primary-600">
              Wedding Invitations
            </h1>
            <div className="space-x-4">
              <Link href="/login" className="text-gray-600 hover:text-primary-600">
                Login
              </Link>
              <Link href="/signup" className="btn-primary">
                Sign Up
              </Link>
            </div>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <div className="text-center">
          <h1 className="text-5xl md:text-6xl font-bold text-gray-900 mb-6">
            Beautiful Digital Wedding
            <span className="text-primary-600"> Invitations</span>
          </h1>
          <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
            Create stunning, personalized wedding invitations with AI-enhanced features.
            Share your special day with guests through unique, animated invitation URLs.
          </p>

          <div className="flex justify-center gap-4">
            <Link href="/signup" className="btn-primary text-lg px-8 py-3">
              Get Started
            </Link>
            <Link href="/login" className="btn-secondary text-lg px-8 py-3">
              Login
            </Link>
          </div>
        </div>

        <div className="mt-20 grid md:grid-cols-3 gap-8">
          <div className="card text-center">
            <div className="text-4xl mb-4">💝</div>
            <h3 className="text-xl font-semibold mb-2">Three Flexible Plans</h3>
            <p className="text-gray-600">
              Choose from Basic, Premium, or Luxury plans based on your guest count
              and budget.
            </p>
          </div>

          <div className="card text-center">
            <div className="text-4xl mb-4">🎨</div>
            <h3 className="text-xl font-semibold mb-2">20 Templates Per Plan</h3>
            <p className="text-gray-600">
              Select from beautiful, professionally designed templates for your
              invitation.
            </p>
          </div>

          <div className="card text-center">
            <div className="text-4xl mb-4">🌍</div>
            <h3 className="text-xl font-semibold mb-2">Country-Aware Pricing</h3>
            <p className="text-gray-600">
              Transparent pricing in your local currency with taxes and fees included.
            </p>
          </div>

          <div className="card text-center">
            <div className="text-4xl mb-4">✨</div>
            <h3 className="text-xl font-semibold mb-2">Personalized Experience</h3>
            <p className="text-gray-600">
              Each guest sees their name in beautiful animations when they open the
              invite.
            </p>
          </div>

          <div className="card text-center">
            <div className="text-4xl mb-4">📍</div>
            <h3 className="text-xl font-semibold mb-2">Embedded Maps</h3>
            <p className="text-gray-600">
              Help guests find your venue with integrated Google Maps location.
            </p>
          </div>

          <div className="card text-center">
            <div className="text-4xl mb-4">📊</div>
            <h3 className="text-xl font-semibold mb-2">Guest Analytics</h3>
            <p className="text-gray-600">
              Track who viewed your invitation and export guest data as CSV.
            </p>
          </div>
        </div>

        <div className="mt-20 bg-white rounded-2xl shadow-xl p-8 md:p-12">
          <h2 className="text-3xl font-bold text-center mb-12">Pricing Plans</h2>

          <div className="grid md:grid-cols-3 gap-8">
            <div className="border-2 border-gray-200 rounded-xl p-6 hover:border-primary-500 transition-colors">
              <h3 className="text-2xl font-bold mb-2">Basic</h3>
              <p className="text-4xl font-bold text-primary-600 mb-4">
                $6<span className="text-lg text-gray-600">/event</span>
              </p>
              <ul className="space-y-3 mb-6">
                <li className="flex items-start">
                  <span className="text-primary-600 mr-2">✓</span>
                  <span>40 regular guests + 5 test opens</span>
                </li>
                <li className="flex items-start">
                  <span className="text-primary-600 mr-2">✓</span>
                  <span>20 beautiful templates</span>
                </li>
                <li className="flex items-start">
                  <span className="text-primary-600 mr-2">✓</span>
                  <span>5-day validity</span>
                </li>
                <li className="flex items-start">
                  <span className="text-primary-600 mr-2">✓</span>
                  <span>Guest analytics</span>
                </li>
              </ul>
            </div>

            <div className="border-2 border-primary-500 rounded-xl p-6 bg-primary-50 relative">
              <div className="absolute -top-3 left-1/2 transform -translate-x-1/2 bg-primary-600 text-white px-4 py-1 rounded-full text-sm">
                Popular
              </div>
              <h3 className="text-2xl font-bold mb-2">Premium</h3>
              <p className="text-4xl font-bold text-primary-600 mb-4">
                $12<span className="text-lg text-gray-600">/event</span>
              </p>
              <ul className="space-y-3 mb-6">
                <li className="flex items-start">
                  <span className="text-primary-600 mr-2">✓</span>
                  <span>100 regular guests + 10 test opens</span>
                </li>
                <li className="flex items-start">
                  <span className="text-primary-600 mr-2">✓</span>
                  <span>20 premium templates</span>
                </li>
                <li className="flex items-start">
                  <span className="text-primary-600 mr-2">✓</span>
                  <span>5-day validity</span>
                </li>
                <li className="flex items-start">
                  <span className="text-primary-600 mr-2">✓</span>
                  <span>Advanced analytics</span>
                </li>
              </ul>
            </div>

            <div className="border-2 border-gray-200 rounded-xl p-6 hover:border-primary-500 transition-colors">
              <h3 className="text-2xl font-bold mb-2">Luxury</h3>
              <p className="text-4xl font-bold text-primary-600 mb-4">
                $20<span className="text-lg text-gray-600">/event</span>
              </p>
              <ul className="space-y-3 mb-6">
                <li className="flex items-start">
                  <span className="text-primary-600 mr-2">✓</span>
                  <span>150 regular guests + 20 test opens</span>
                </li>
                <li className="flex items-start">
                  <span className="text-primary-600 mr-2">✓</span>
                  <span>20 luxury templates</span>
                </li>
                <li className="flex items-start">
                  <span className="text-primary-600 mr-2">✓</span>
                  <span>5-day validity</span>
                </li>
                <li className="flex items-start">
                  <span className="text-primary-600 mr-2">✓</span>
                  <span>Premium support</span>
                </li>
              </ul>
            </div>
          </div>

          <p className="text-center text-gray-500 mt-8 text-sm">
            Prices exclude taxes and service fees. Final price calculated based on your
            country.
          </p>
        </div>
      </div>

      <footer className="bg-gray-900 text-white py-8 mt-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <p>Wedding Invitations Platform - AI-Enhanced Digital Invitations</p>
          <p className="text-gray-400 mt-2">Make your special day unforgettable</p>
        </div>
      </footer>
    </main>
  );
}
