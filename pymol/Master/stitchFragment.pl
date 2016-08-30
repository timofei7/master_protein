use GENERAL;
use Getopt::Long;
use PDB;

# process command line arguments
my $usage = GENERAL::usage("Stitches a given fragment to an existing structure, using specified fixed anchors on the fragment and the structure.",
                           "Required switches:", "", "-s", "structure to stitch to",
                           "-f", "fragments to stitch with",
                           "--or", "order of stitching. N or C depending on whether the fragment is to be stitched N- or C-terminally with respect to the structure.",
                           "--sa", "anchor residues on the structure (e.g., 'A12 A13'). Can specify up to two, e.g., --sa 'A12 A13' --sa 'A17 A18', for ".
                                   "cases where the fragment is to be stitched in two places (i.e., as a bridge).",
                           "--fa", "anchor residues on the fragment (e.g., 'A12 A13'). Can specify two. The number of structure and fragment achors has to agree.",
                           "--gapLen", "the length of the desired gap between structure and fragment anchoring residues. Can be a range (e.g., \"--gapLen '1-3'\"). ".
                                     "Again, there has to be as many of these as there are sets of anchoring residues.",
                           "-o", "output file name for the stitched structure.");
my %opts;
{ my @tmp; $opts{fa} = \@tmp; }
{ my @tmp; $opts{sa} = \@tmp; }
{ my @tmp; $opts{gapLen} = \@tmp; }
GetOptions(\%opts, "s=s", "or=s", "o=s", "f=s", "sa=s" => $opts{sa}, "fa=s" => $opts{fa}, "gapLen=s" => $opts{gapLen});
if (!defined($opts{s}) || !defined($opts{f}) || !defined($opts{sa}) || (scalar(@{$opts{fa}}) == 0) || (scalar(@{$opts{sa}}) == 0) || 
    (scalar(@{$opts{fa}}) != scalar(@{$opts{sa}})) || (scalar(@{$opts{fa}}) > 2) || (scalar(@{$opts{sa}}) > 2) ||
    ($opts{or} !~ /^[NC]$/) || !defined($opts{gapLen}) || (scalar(@{$opts{fa}}) != scalar(@{$opts{gapLen}})) || !defined($opts{o})) {
  die $usage;
}
my $tol = 0.1;
my $Nc = 100;

# read in structures and identify anchor points
my $struct = PDB::new($opts{s});
my $frag = PDB::new($opts{f});
my @stAnchs = cloneAnchors($struct, $opts{sa});

# now iterate to find bridges to connect corresponding anchor points
for (my $c = 1; $c <= $Nc; $c++) {
  # copy anchors of the fragment inside the loop, because the fragment may move from one cycle to the next
  my @frAnchs = cloneAnchors($frag, $opts{fa});

  # visit all anchor sets (either one or two)
  my (@best, @rmsd, @ord);
  for (my $ai = 0; $ai < scalar(@stAnchs); $ai++) {
    # form  the query consisting of structure and fragment anchors
    my $qpdb = PDB::new();
    my $nchA = $qpdb->_newChain("A");
    my $nchB = $qpdb->_newChain("B");
    if ((($opts{or} eq "C") && ($ai == 0)) || (($opts{or} eq "N") && ($ai == 1))) {
      PDB::copyChain($stAnchs[$ai]->{chain}->[0], $nchA);
      PDB::copyChain($frAnchs[$ai]->{chain}->[0], $nchB);
      push(@ord, 1);
    } else {
      PDB::copyChain($frAnchs[$ai]->{chain}->[0], $nchA);
      PDB::copyChain($stAnchs[$ai]->{chain}->[0], $nchB);
      push(@ord, 2);
    }

    # search this query and store best match and its RMSD
    my ($best, $rmsd) = searchWithMASTER($qpdb, $opts{gapLen}->[$ai]);
    push(@best, $best); push(@rmsd, $rmsd);
  }

  # is the stitch good enough?
  if (GENERAL::max(\@rmsd) <= $tol) {
    printf("Cycle $c converged with RMSD(s) [%s]. Stitching...\n", join(" and ", @rmsd));
    # if so, merge the fragment by copying the bridging positions from the found best match
    my $pdb = PDB::new();

    if (scalar(@stAnchs) == 1) {
      if ($opts{or} eq "C") {
        fuseByCopy($pdb, $struct, $frag, $stAnchs[0], $frAnchs[0], $best[0]);
      } else {
        fuseByCopy($pdb, $frag, $struct, $frAnchs[0], $stAnchs[0], $best[0]);
      }
    } else {
      my $pdbtmp = PDB::new();
      my $ai = (($opts{or} eq "C") ? 0 : 1);
      fuseByCopy($pdbtmp, $struct, $frag, $stAnchs[$ai], $frAnchs[$ai], $best[$ai]);
      fuseByCopy($pdb, $pdbtmp, $struct, $frAnchs[!$ai], $stAnchs[!$ai], $best[!$ai], 1, 0);
    }
    $pdb->writePDB($opts{o}, "");
    last;
  } else {
    # if not, align the fragment onto the positions of the top match via its anchoring residues
    my @frAtoms = concatenateBackboneAtomsFromPDBs(@frAnchs);
    my @matchAtoms;
    for (my $ai = 0; $ai < scalar(@best); $ai++) {
      my $n = scalar($best[$ai]->ConRes());
      my $ni = scalar($frAnchs[$ai]->ConRes());
      my @range = ($ord[$ai] == 1) ? (($n - $ni) .. ($n - 1)) : (0 .. ($ni - 1));
      push(@matchAtoms, concatenateBackboneAtomsFromResidues(residueSubset($best[$ai], \@range)));
    }
    my $mrms = PDB::superimpose(\@frAtoms, \@matchAtoms, $frag);
    printf("Cycle $c gave RMSD(s) [%s]. Adjusted fragment by RMSD of %f\n", join(" and ", @rmsd), $mrms);
    if ($c == $Nc) { printf("Failed to stitch!\n"); }
  }
}

sub searchWithMASTER {
  my $qpdb = shift;
  my $L = shift;
  my $cut = 0.5;

  # create PDS file
  my $base = "_123_srch";
  my $qpdbf = "$base.pdb";
  my $qpdsf = "$base.pds";
  my $sdir = "$base.struct";
  $qpdb->writePDB($qpdbf, "");
  GENERAL::csystem("/home/grigoryanlab/library/MASTER/bin/createPDS --type query --pdb $qpdbf");

  # search
  my $db = "/home/glab/bc-30-sc-correct-20141022-fullBB/list";
  GENERAL::csystem("/home/grigoryanlab/library/MASTER/bin/master --query $qpdsf --targetList $db --rmsdCut $cut --bbRMSD --topN 10 --structOut $sdir --gapLen $L --outType wgap | grep -v Visiting");

  # read best match
  my $topF = "$sdir/wgap01.pdb";
  GENERAL::assert(-e $topF, "Looks hard to stitch, not finding any good matches. Bad starting point?");
  my $best = PDB::new($topF);
  my $rmsdLine = `grep REMARK $topF`;
  my @rmsdLine = split(" ", GENERAL::Trim($rmsdLine));
  my $rmsd = $rmsdLine[1];
  GENERAL::assert(GENERAL::isNumeric($rmsd), "could not parse out RMSD from REMARK in top match, '$rmsdLine'");

  # clean up
  GENERAL::crm($qpdbf, $qpdsf);
  GENERAL::csystem("rm -r $sdir");

  # return
  return ($best, $rmsd);
}

sub isBackbone {
  my $a = shift;
  return ($a->{atomname} =~ /^(N|C|CA|O)$/);
}

sub concatenateBackboneAtomsFromPDBs {
  my @bb;
  foreach my $pdb (@_) {
    foreach my $ch (@{$pdb->{chain}}) {
      foreach my $res (@{$ch->{res}}) {
        foreach my $a (@{$res->{atom}}) {
          push(@bb, $a) if (isBackbone($a));
        }
      }
    }
  }
  return @bb;
}

sub concatenateBackboneAtomsFromResidues {
  my @bb;
  foreach my $res (@_) {
    foreach my $a (@{$res->{atom}}) {
      push(@bb, $a) if (isBackbone($a));
    }
  }
  return @bb;
}

sub residueSubset {
  my $pdb = shift;
  my $idx = shift;
  my @res = $pdb->ConRes();
  return @res[@$idx];
}

sub fuseByCopy {
  my $pdb = shift;
  my $pdbN = shift;  # N-terminal fusion partner
  my $pdbC = shift;  # C-terminal fusion partner
  my $anchN = shift;
  my $anchC = shift;
  my $bridge = shift;
  my $copyOtherN = shift;
  my $copyOtherC = shift;
  $copyOtherN = 1 if (!defined($copyOtherN));
  $copyOtherC = 1 if (!defined($copyOtherC));
  my @anchN = $anchN->ConRes();
  my @anchC = $anchC->ConRes();
  my @bridge = $bridge->ConRes();

  # first, copy over any chains not involved in the bridging
  for (my $ii = 0; $ii < 2; $ii++) {
    my $pdbT = ($ii == 0) ? $pdbN : $pdbC;
    next if ((!$ii && !$copyOtherN) || ($ii && !$copyOtherC));
    foreach my $ch (@{$pdbT->{chain}}) {
      if (!defined($ch->{fused})) {
        my $nch = $pdb->_newChain($ch->{id});
        PDB::copyChain($ch, $nch);
      }
    }
  }

  # then copy the N-terminal part of the N-terminal fusion partner
  my $chain = findFusionChain($pdbN);
  my $nch = $pdb->_newChain($chain->{id});
  $nch->{fused} = 1;
  foreach my $res (@{$chain->{res}}) {
    my $nr = PDB::_newResidue($res->{resname}, $res->{resnum}, $res->{iresnum}, $res->{uresnum}, $nch);
    PDB::copyResidue($res, $nr);      
    # keep copying until the last (most C-terminal) anchor residue
    if (PDB::atomDist(PDB::getAtomInRes($res, "CA"), PDB::getAtomInRes($anchN[-1], "CA")) == 0) { last; }
  }

  # then copy the gap straight from the bridge
  # the residues of the bridge are: [residues matching the N-terminal anchor] [gap residues] [residues matching the C-terminal anchor]
  for (my $ri = scalar(@anchN); $ri < scalar(@bridge) - scalar(@anchC); $ri++) {
    my $res = $bridge[$ri];
    my $nr = PDB::_newResidue($res->{resname}, $res->{resnum}, $res->{resnum}, $res->{uresnum}, $nch);
    PDB::copyResidue($res, $nr);
    my $lres = $nch->{res}->[-2];
    $nr->{resnum} = $lres->{resnum} + 1; $nr->{iresnum} = $lres->{iresnum} + 1; $nr->{uresnum} = $lres->{uresnum} + 1;
  }

  # finally, bring in the C-terminal part from the C-terminal fusion partner
  $chain = findFusionChain($pdbC);
  my $copy = 0;
  foreach my $res (@{$chain->{res}}) {
    # start copying at the first (most N-terminal) anchor residue
    if (!$copy) {
      if (PDB::atomDist(PDB::getAtomInRes($res, "CA"), PDB::getAtomInRes($anchC[0], "CA")) == 0) { $copy = 1; }
    }
    if ($copy) {
      my $nr = PDB::_newResidue($res->{resname}, $res->{resnum}, $res->{iresnum}, $res->{uresnum}, $nch);
      PDB::copyResidue($res, $nr);
      my $lres = $nch->{res}->[-2];
      $nr->{resnum} = $lres->{resnum} + 1; $nr->{iresnum} = $lres->{iresnum} + 1; $nr->{uresnum} = $lres->{uresnum} + 1;
    }
  }
}

sub findFusionChain {
  my $pdb = shift;
  foreach my $ch (@{$pdb->{chain}}) {
    if (defined($ch->{fused})) { return $ch; }
  }
  GENERAL::error("could not find fusion chain!");
}

sub cloneAnchors {
  my $pdb = shift;
  my $anchs = shift;
  my @apdbs;

  for (my $i = 0; $i < scalar(@$anchs); $i++) {
    my @ares = split(" ", GENERAL::Trim($anchs->[$i]));
    $pdb->resetValidResidues(0);
    foreach my $ares (@ares) {
      GENERAL::assert(($ares =~ /^(\D+)(\d+)$/) ? 1 : 0, "could not parse position '$ares'");
      my $cid = $1;
      my $rid = $2;
      my $res = $pdb->getResByInd($cid, $rid, 1, 3);
      $res->{valid} = 1;
      $res->{chain}->{fused} = 1;
    }
    my $apdb = $pdb->clone(1);
    GENERAL::assert(scalar(@{$apdb->{chain}}) == 1, "an anchor involves residues in multiple chains!");
    push(@apdbs, $apdb);
  }
  return @apdbs;
}
