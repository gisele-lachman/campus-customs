import { Bulldog } from '../components/Graphics'

export default function About() {
  return (
    <>
      <header className="page-banner">
        <span className="kicker">Our story</span>
        <h1>About Campus Customs</h1>
        <p className="accent">A campus store with a varsity heart</p>
      </header>
      <div className="prose reveal">
        <p>
          Campus Customs started with a simple idea: everyone who loves Yale should be able to find gear that feels like it
          belongs on campus. We’re a small, student-minded shop that celebrates the traditions, colleges, and teams that
          make Yale feel like home.
        </p>

        <h2>What we carry</h2>
        <p>
          Our shelves are stocked with the classics: navy hoodies with big block letters, cozy quarter-zips, crewnecks for
          every residential college and graduate school, and tees for cheering on the Bulldogs from the stands. We also make
          room for the people who cheer loudest from home, with pieces for parents, grandparents, aunts, uncles, and cousins.
        </p>

        <h2>Why we do it</h2>
        <p>
          Yale pride shows up in small moments: a sweatshirt pulled on before an early seminar, a college shirt worn to an
          intramural game, a gift sent to a family member who has never missed The Game. We want every piece we sell to be
          part of those moments, comfortable enough to live in and meaningful enough to keep long after graduation.
        </p>

        <h2>How we help</h2>
        <p>
          Every product page shows exactly which sizes are in stock, so there are no surprises. And if you’re not sure what
          to pick, our Bulldog shopping assistant is a click away in the corner of every page.
        </p>

        <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginTop: 28 }}>
          <Bulldog size={64} />
          <p className="signoff" style={{ margin: 0 }}>Boola boola, and thanks for shopping with us.</p>
        </div>
      </div>
    </>
  )
}
